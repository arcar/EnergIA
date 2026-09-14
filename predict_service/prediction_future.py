"""
Étape 5 du pipeline de prédiction : générer de vraies prévisions dans le
futur (au-delà des données disponibles) avec un modèle déjà entraîné par
04_train_random_forest.py.

Point crucial à comprendre avant d'utiliser ce script : un modèle entraîné
à l'horizon H (ex. "1mois") n'est fiable que pour des dates cibles situées
entre la dernière date connue (exclue) et cette dernière date + H. Au-delà,
son lag le plus court utilisable (lag_1mois) réclamerait une valeur qui
n'existe pas encore réellement — ce serait soit une fuite fictive, soit il
faudrait ré-injecter une prédiction précédente comme si c'était une vraie
donnée (prévision récursive), ce qui accumule l'erreur à chaque pas et
n'est PAS ce que fait ce script.

Concrètement :
  - un modèle "1mois" ne peut prédire QUE jusqu'à dernière_date + 1 mois
  - un modèle "1an" peut prédire n'importe quelle date jusqu'à
    dernière_date + 1 an, car lag_1an renvoie alors toujours vers une date
    déjà réellement connue.
  => Pour "des prédictions précises avec la possibilité d'aller jusqu'à un
     an" sur toute la période, c'est le modèle entraîné avec HORIZON="1an"
     qu'il faut utiliser ici (charger modele_random_forest_1an.joblib).

Le script :
  1. Détecte la dernière date réellement connue dans fait_energie.
  2. Construit la grille de dates cibles (toutes les régions x demi-heures)
     entre cette date et dernière_date + horizon du modèle chargé.
  3. Reconstruit exactement les mêmes features qu'à l'entraînement :
     calendaires (calculées directement, aucune donnée requise), vacances
     scolaires (jointes depuis dim_vacances : ERREUR EXPLICITE si le
     calendrier ne couvre pas encore les dates cibles), variables
     régionales (tx_chauffage_elec/climatisation/population : valeur de
     l'année cible si connue dans dim_region, sinon on FIGE sur la
     dernière année connue en avertissant clairement), et les lags requis
     par le modèle (calculés par jointure vers les vraies données passées
     de fait_energie, jamais vers des prédictions).
  4. Applique le modèle et exporte les prévisions.

Entrée  : etl_analytique/predictions/modele_random_forest_{HORIZON}.joblib
Sortie  : etl_analytique/predictions/previsions_{HORIZON}.csv
          etl_analytique/predictions/previsions_{HORIZON}.png
"""

import duckdb
import numpy as np
import pandas as pd
from pandas.tseries.offsets import DateOffset
import matplotlib.pyplot as plt
import joblib

# ---------------------------------------------------------------------
# Horizon du modèle à charger : doit correspondre à un modèle déjà
# entraîné par 04_train_random_forest.py (HORIZON="1an" recommandé pour
# des prévisions sur toute l'année à venir)
HORIZON = "1an"
# ---------------------------------------------------------------------

DB_PATH = "base_analytique.duckdb"
MODEL_PATH = f"predict_service/predictions/modele_random_forest_{HORIZON}.joblib"
OUTPUT_CSV = f"predict_service/predictions/previsions_{HORIZON}.csv"
OUTPUT_PNG = f"predict_service/predictions/previsions_{HORIZON}.png"

ANNEES_DIM_REGION = list(range(2021, 2027))

DECALAGE_PAR_HORIZON = {
    "1h": DateOffset(hours=1),
    "1j": DateOffset(days=1),
    "1semaine": DateOffset(weeks=1),
    "1mois": DateOffset(months=1),
    "1an": DateOffset(years=1),
}

# Décalage calendaire correspondant à chaque colonne de lag, pour calculer
# sa valeur par jointure vers les vraies données passées
DECALAGE_PAR_LAG = {
    "lag_1h": DateOffset(hours=1),
    "lag_1j": DateOffset(days=1),
    "lag_1semaine": DateOffset(weeks=1),
    "lag_1mois": DateOffset(months=1),
    "lag_1an": DateOffset(years=1),
}

COLONNES_BOOL = [
    "weekend", "printemps", "ete", "automne", "hiver",
    "vacances_zone_a", "vacances_zone_b", "vacances_zone_c",
]


def charger_modele():
    paquet = joblib.load(MODEL_PATH)
    modele = paquet["modele"]
    colonnes = paquet["colonnes"]
    horizon_entraine = paquet.get("horizon", HORIZON)
    if horizon_entraine != HORIZON:
        print(f"/!\\ Attention : le modèle chargé a été entraîné avec HORIZON="
              f"{horizon_entraine!r}, différent du HORIZON={HORIZON!r} configuré ici.")
    return modele, colonnes, horizon_entraine


def construire_grille_cible(con, horizon: str):
    derniere_date = con.execute(
        "SELECT MAX(date) FROM dim_temps t JOIN fait_energie f ON f.id_temps = t.id_temps"
    ).fetchone()[0]
    derniere_date = pd.Timestamp(derniere_date)
    date_limite = derniere_date + DECALAGE_PAR_HORIZON[horizon]

    print(f"Dernière date connue dans fait_energie : {derniere_date.date()}")
    print(f"Horizon du modèle : {horizon} -> prévisions valides jusqu'au {date_limite.date()} inclus")

    # Seules les régions ayant un historique réel dans fait_energie peuvent être
    # prévues : une région présente dans dim_region mais absente de fait_energie
    # (ex. la Corse, hors du réseau interconnecté suivi par RTE éCO2mix) n'a
    # jamais servi à l'entraînement (le one-hot "region_..." correspondant n'existe
    # pas dans colonnes_modele) et n'a aucune donnée passée pour calculer ses lags.
    regions = con.execute("""
        SELECT DISTINCT dr.id_region, dr.region, dr.zone_scolaire
        FROM dim_region dr
        WHERE EXISTS (SELECT 1 FROM fait_energie f WHERE f.id_region = dr.id_region)
    """).df()

    toutes_regions = con.execute("SELECT id_region, region FROM dim_region").df()
    regions_exclues = toutes_regions.loc[
        ~toutes_regions["id_region"].isin(regions["id_region"]), "region"
    ].tolist()
    if regions_exclues:
        print(f"/!\\ Région(s) présente(s) dans dim_region mais sans historique dans "
              f"fait_energie, donc exclue(s) des prévisions : {regions_exclues}")

    demi_heures = pd.date_range("00:00", "23:30", freq="30min").time
    dates_cibles = pd.date_range(
        derniere_date + pd.Timedelta(days=1), date_limite, freq="D"
    )
    if len(dates_cibles) == 0:
        raise ValueError(
            f"Aucune date à prévoir : dernière_date + horizon ({date_limite.date()}) "
            f"n'est pas postérieure à dernière_date + 1 jour. Vérifie HORIZON."
        )

    grille = pd.MultiIndex.from_product(
        [regions["id_region"], dates_cibles, demi_heures],
        names=["id_region", "date", "heure"],
    ).to_frame(index=False)
    grille = grille.merge(regions, on="id_region", how="left")
    grille["date"] = pd.to_datetime(grille["date"])

    return grille, derniere_date, date_limite


def ajouter_variables_calendaires(grille: pd.DataFrame) -> pd.DataFrame:
    heure_decimale = grille["heure"].apply(lambda h: h.hour + h.minute / 60.0)
    grille["heure_decimale"] = heure_decimale
    grille["year"] = grille["date"].dt.year
    grille["month"] = grille["date"].dt.month
    grille["trimestre"] = (grille["month"] - 1) // 3 + 1
    grille["day"] = grille["date"].dt.day
    grille["week"] = grille["date"].dt.isocalendar().week.astype(int)
    grille["day_week_number"] = grille["date"].dt.weekday
    grille["weekend"] = grille["day_week_number"] >= 5
    grille["printemps"] = grille["month"].isin([3, 4, 5])
    grille["ete"] = grille["month"].isin([6, 7, 8])
    grille["automne"] = grille["month"].isin([9, 10, 11])
    grille["hiver"] = grille["month"].isin([12, 1, 2])

    grille["heure_sin"] = np.sin(2 * np.pi * grille["heure_decimale"] / 24.0)
    grille["heure_cos"] = np.cos(2 * np.pi * grille["heure_decimale"] / 24.0)
    grille["jour_semaine_sin"] = np.sin(2 * np.pi * grille["day_week_number"] / 7.0)
    grille["jour_semaine_cos"] = np.cos(2 * np.pi * grille["day_week_number"] / 7.0)
    grille["mois_sin"] = np.sin(2 * np.pi * grille["month"] / 12.0)
    grille["mois_cos"] = np.cos(2 * np.pi * grille["month"] / 12.0)
    return grille


def ajouter_vacances(con, grille: pd.DataFrame) -> pd.DataFrame:
    vac = con.execute(
        "SELECT date, vacances_zone_a, vacances_zone_b, vacances_zone_c FROM dim_vacances"
    ).df()
    vac["date"] = pd.to_datetime(vac["date"])

    grille = grille.merge(vac, on="date", how="left")

    dates_manquantes = grille.loc[grille["vacances_zone_a"].isna(), "date"].unique()
    if len(dates_manquantes) > 0:
        raise ValueError(
            f"{len(dates_manquantes)} date(s) cible(s) ne sont pas couvertes par "
            f"dim_vacances (calendrier scolaire pas assez à jour), ex. : "
            f"{sorted(pd.Series(dates_manquantes).dt.date)[:5]}. "
            f"Il faut mettre à jour la source des vacances scolaires pour couvrir "
            f"cette période avant de pouvoir prévoir dessus."
        )
    return grille


def ajouter_variables_regionales(con, grille: pd.DataFrame) -> pd.DataFrame:
    dr = con.execute("SELECT * FROM dim_region").df()
    derniere_annee_connue = max(ANNEES_DIM_REGION)

    resultats = []
    for annee_cible, sous_grille in grille.groupby("year"):
        annee_source = annee_cible if annee_cible in ANNEES_DIM_REGION else derniere_annee_connue
        if annee_source != annee_cible:
            print(f"/!\\ Pas de tx_chauffage_elec/climatisation/population connus pour "
                  f"{annee_cible} dans dim_region : valeurs de {annee_source} réutilisées "
                  f"(hypothèse : pas d'évolution au-delà de la dernière année connue).")

        cols = ["id_region",
                f"tx_chauffage_elec_{annee_source}",
                f"tx_climatisation_{annee_source}",
                f"population_{annee_source}"]
        dr_annee = dr[cols].rename(columns={
            f"tx_chauffage_elec_{annee_source}": "tx_chauffage_elec",
            f"tx_climatisation_{annee_source}": "tx_climatisation",
            f"population_{annee_source}": "population",
        })
        resultats.append(sous_grille.merge(dr_annee, on="id_region", how="left"))

    return pd.concat(resultats, ignore_index=True)


def ajouter_lags(con, grille: pd.DataFrame, colonnes_modele: list[str]) -> pd.DataFrame:
    lags_requis = [c for c in colonnes_modele if c in DECALAGE_PAR_LAG]
    if not lags_requis:
        return grille

    historique = con.execute("""
        SELECT f.id_region, t.date, t.heure, f.consommation_mw
        FROM fait_energie f
        JOIN dim_temps t ON f.id_temps = t.id_temps
    """).df()
    historique["date"] = pd.to_datetime(historique["date"])

    for lag_col in lags_requis:
        decalage = DECALAGE_PAR_LAG[lag_col]
        tmp = grille[["id_region", "date", "heure"]].copy()
        tmp["date_source"] = tmp["date"] - decalage
        merged = tmp.merge(
            historique.rename(columns={"date": "date_source", "consommation_mw": lag_col}),
            on=["id_region", "date_source", "heure"],
            how="left",
        )
        grille[lag_col] = merged[lag_col].values

        nb_manquants = grille[lag_col].isna().sum()
        if nb_manquants > 0:
            raise ValueError(
                f"{nb_manquants} valeur(s) de {lag_col} introuvables dans l'historique "
                f"réel de fait_energie : ce modèle (horizon {HORIZON}) ne peut pas "
                f"prédire au-delà de dernière_date + {HORIZON}."
            )

    return grille


def preparer_features(grille: pd.DataFrame, colonnes_modele: list[str]) -> pd.DataFrame:
    X = grille.copy()

    for col in COLONNES_BOOL:
        if col in X.columns:
            X[col] = X[col].astype(int)

    if "zone_scolaire" in X.columns:
        X = pd.get_dummies(X, columns=["zone_scolaire"], prefix="zone")
    if "region" in X.columns:
        X = pd.get_dummies(X, columns=["region"], prefix="region")

    for col in X.columns:
        if X[col].dtype == bool:
            X[col] = X[col].astype(int)

    # Réalignement strict sur les colonnes vues à l'entraînement
    X = X.reindex(columns=colonnes_modele, fill_value=0)
    return X


def main():
    modele, colonnes_modele, horizon_entraine = charger_modele()
    print(f"Modèle chargé : {MODEL_PATH} (entraîné à l'horizon {horizon_entraine}, "
          f"{len(colonnes_modele)} features attendues)")

    con = duckdb.connect(DB_PATH, read_only=True)

    grille, derniere_date, date_limite = construire_grille_cible(con, horizon_entraine)
    print(f"{len(grille):,} points à prévoir (toutes régions, demi-heure par demi-heure).")

    grille = ajouter_variables_calendaires(grille)
    grille = ajouter_vacances(con, grille)
    grille = ajouter_variables_regionales(con, grille)
    grille = ajouter_lags(con, grille, colonnes_modele)

    con.close()

    X = preparer_features(grille, colonnes_modele)
    grille["consommation_predite"] = modele.predict(X)

    resultat = grille[["id_region", "region", "date", "heure", "consommation_predite"]]
    resultat.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\nPrévisions écrites : {OUTPUT_CSV}")
    print(resultat.head())

    # Graphique : une région, toute la période prévue
    premiere_region = resultat["id_region"].iloc[0]
    courbe = resultat[resultat["id_region"] == premiere_region].copy()
    courbe["horodatage"] = pd.to_datetime(courbe["date"].astype(str) + " " + courbe["heure"].astype(str))
    courbe = courbe.sort_values("horodatage")

    plt.figure(figsize=(14, 6))
    plt.plot(courbe["horodatage"], courbe["consommation_predite"], linewidth=0.8)
    plt.xlabel("Date")
    plt.ylabel("Consommation prédite (MW)")
    plt.title(f"Prévision {horizon_entraine} - région {courbe['region'].iloc[0]} "
              f"({derniere_date.date()} -> {date_limite.date()})")
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=150)
    print(f"Graphique écrit : {OUTPUT_PNG}")


if __name__ == "__main__":
    main()