"""
Étape 1 du pipeline de prédiction : variables temporelles (encodage
cyclique) + variables retardées à PLUSIEURS horizons (1h, 1 jour,
1 semaine, 1 mois, 1 an).

Pourquoi plusieurs lags plutôt qu'un seul : on veut pouvoir prédire à
différents horizons (de quelques heures à un an), et à chaque horizon
correspond un lag "juste assez ancien" pour être exploitable sans fuite
de données. Par exemple, pour prédire à 1 mois, on peut légitimement
utiliser lag_1mois (et lag_1an), mais pas lag_1semaine ni lag_1j : ces
derniers décrivent des instants situés ENTRE le moment de la prédiction
et sa cible, donc pas encore connus en situation réelle. C'est
04_train_random_forest.py (paramètre HORIZON) qui se charge de ne garder,
pour l'entraînement, que les lags valides pour l'horizon choisi.

  - lag_1h, lag_1j, lag_1semaine : décalages "physiques" de 2, 48 et 336
    demi-heures — calculés par fonction fenêtre LAG(), correct car la
    série est à pas régulier de 30 min sans trou.
  - lag_1mois, lag_1an : décalages calendaires (un mois ou un an avant,
    à la même date/heure) — calculés par auto-jointure sur
    (id_region, heure, date - INTERVAL ...), plus robuste qu'un décalage
    de lignes fixe car les mois n'ont pas tous la même longueur et il
    faut gérer les années bissextiles.

Les lignes sans historique suffisant (lag_1an indisponible : première
année de chaque région) sont supprimées avant export.

Sortie : etl_analytique/predictions/dataset_features.csv
"""

import duckdb
import numpy as np
import pandas as pd

DB_PATH = "base_analytique.duckdb"
OUTPUT_CSV = "predict_service/predictions/dataset_features.csv"

ANNEES_DIM_REGION = range(2021, 2027)


def build_region_annee_sql() -> str:
    """Dépivote dim_region (une colonne par année) en format long
    (une ligne par région x année)."""
    parts = []
    for annee in ANNEES_DIM_REGION:
        parts.append(f"""
        SELECT
            id_region,
            {annee} AS annee,
            tx_chauffage_elec_{annee} AS tx_chauffage_elec,
            tx_climatisation_{annee}  AS tx_climatisation,
            population_{annee}        AS population
        FROM dim_region
        """)
    return "\nUNION ALL\n".join(parts)


def build_query() -> str:
    region_annee_sql = build_region_annee_sql()

    return f"""
        WITH region_annee AS (
            {region_annee_sql}
        ),

        base AS (
            SELECT
                f.id_region,
                f.id_temps,
                f.consommation_mw,
                f.production_nucleaire_mw,
                f.production_eolienne_mw,
                f.production_solaire_mw,

                t.date,
                t.heure,
                t.year,
                t.trimestre,
                t.month,
                t.day,
                t.week,
                t.day_week_number,
                EXTRACT(HOUR FROM t.heure) + EXTRACT(MINUTE FROM t.heure) / 60.0 AS heure_decimale,
                t.weekend,
                t.printemps,
                t.ete,
                t.automne,
                t.hiver,

                v.vacances_zone_a,
                v.vacances_zone_b,
                v.vacances_zone_c,

                dr.region,
                dr.zone_scolaire,
                ra.tx_chauffage_elec,
                ra.tx_climatisation,
                ra.population

            FROM
                fait_energie f
            JOIN dim_temps t
                ON f.id_temps = t.id_temps
            JOIN dim_vacances v
                ON t.id_vacances = v.id_vacances
            JOIN dim_region dr
                ON f.id_region = dr.id_region
            JOIN region_annee ra
                ON f.id_region = ra.id_region AND t.year = ra.annee
        )

        SELECT
            b.* EXCLUDE (heure),

            -- Encodage cyclique (sin/cos) des variables temporelles périodiques
            SIN(2 * PI() * b.heure_decimale / 24.0) AS heure_sin,
            COS(2 * PI() * b.heure_decimale / 24.0) AS heure_cos,
            SIN(2 * PI() * b.day_week_number / 7.0) AS jour_semaine_sin,
            COS(2 * PI() * b.day_week_number / 7.0) AS jour_semaine_cos,
            SIN(2 * PI() * b.month / 12.0)          AS mois_sin,
            COS(2 * PI() * b.month / 12.0)          AS mois_cos,

            -- Lags "physiques" (pas de temps fixe, sûrs car série régulière)
            LAG(b.consommation_mw, 2)   OVER w AS lag_1h,
            LAG(b.consommation_mw, 48)  OVER w AS lag_1j,
            LAG(b.consommation_mw, 336) OVER w AS lag_1semaine,

            -- Lags calendaires (auto-jointure, robustes aux mois inégaux / bissextiles)
            prev_mois.consommation_mw AS lag_1mois,
            prev_an.consommation_mw   AS lag_1an

        FROM
            base b
        LEFT JOIN
            base prev_mois
            ON  prev_mois.id_region = b.id_region
            AND prev_mois.heure     = b.heure
            AND prev_mois.date      = b.date - INTERVAL 1 MONTH
        LEFT JOIN
            base prev_an
            ON  prev_an.id_region = b.id_region
            AND prev_an.heure     = b.heure
            AND prev_an.date      = b.date - INTERVAL 1 YEAR
        WINDOW
            w AS (PARTITION BY b.id_region ORDER BY b.id_temps)
        ORDER BY
            b.id_region, b.id_temps
    """


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("Construction du dataset (variables cycliques + lags 1h/1j/1semaine/1mois/1an)...")
    df = con.execute(build_query()).df()
    print(f"{len(df):,} lignes avant nettoyage des débuts de série.")

    con.close()

    # lag_1an est la contrainte la plus forte (1 an d'historique nécessaire) :
    # si elle est disponible, lag_1h/1j/1semaine/1mois le sont forcément aussi.
    # On retire en plus les quelques dates où lag_1mois est NULL (rares cas
    # de bord liés aux mois de longueur inégale, ex. 31 -> mois à 30 jours).
    colonnes_requises = ["lag_1an", "lag_1mois"]
    nb_avant = len(df)
    df = df.dropna(subset=colonnes_requises)
    nb_apres = len(df)
    print(f"{nb_avant - nb_apres:,} lignes supprimées (historique insuffisant pour "
          f"lag_1an et/ou lag_1mois).")
    print(f"{nb_apres:,} lignes conservées.")

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\nFichier écrit : {OUTPUT_CSV}")
    print(f"\nColonnes finales ({df.shape[1]}) :")
    print(list(df.columns))


if __name__ == "__main__":
    main()