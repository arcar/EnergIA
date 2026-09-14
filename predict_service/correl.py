"""
Étape 2 du pipeline de prédiction (nouvelle version) : matrice de
corrélation calculée sur le dataset ENRICHI produit par l'étape 1
(etl_analytique/predictions/dataset_features.csv), qui contient déjà :
  - les variables temporelles brutes (year, month, weekend, ...)
  - leur encodage cyclique (heure_sin/cos, jour_semaine_sin/cos, mois_sin/cos)
  - les variables retardées (lag_30min, lag_veille, lag_semaine)
  - les moyennes mobiles de tendance (moy_mobile_24h, moy_mobile_7j)
  - les variables régionales (tx_chauffage_elec, tx_climatisation, population, zone_scolaire)

Contrairement à la première version (qui interrogeait directement
base_analytique.duckdb), ce script part du CSV déjà construit à l'étape 1 :
il faut donc exécuter 01_feature_engineering.py avant celui-ci.

Sorties :
    etl_analytique/predictions/matrice_correlation.csv  (matrice complète)
    etl_analytique/predictions/correlation_consommation.png (heatmap)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_CSV = "predict_service/predictions/dataset_features.csv"
OUTPUT_CSV = "predict_service/predictions/matrice_correlation.csv"
OUTPUT_PNG = "predict_service/predictions/correlation_consommation.png"

# Colonnes à exclure de la matrice : identifiants et texte libre, pas des
# variables explicatives numériques ou catégorielles à corréler
COLONNES_A_EXCLURE = ["id_region", "id_temps", "date", "region"]


def prepare_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Convertit le dataset en un dataframe entièrement numérique,
    exploitable par .corr() : bool -> 0/1, zone_scolaire -> one-hot."""
    df_num = df.drop(columns=[c for c in COLONNES_A_EXCLURE if c in df.columns])

    colonnes_bool = [
        "weekend", "printemps", "ete", "automne", "hiver",
        "vacances_zone_a", "vacances_zone_b", "vacances_zone_c",
    ]
    for col in colonnes_bool:
        if col in df_num.columns:
            df_num[col] = df_num[col].astype(int)

    if "zone_scolaire" in df_num.columns:
        df_num = pd.get_dummies(df_num, columns=["zone_scolaire"], prefix="zone")

    for col in df_num.columns:
        if df_num[col].dtype == bool:
            df_num[col] = df_num[col].astype(int)

    return df_num


def main():
    print(f"Lecture de {INPUT_CSV} ...")
    df = pd.read_csv(INPUT_CSV)
    print(f"{len(df):,} lignes, {df.shape[1]} colonnes chargées.")

    df_num = prepare_numeric(df)

    print("\nCalcul de la matrice de corrélation...")
    matrice_corr = df_num.corr(numeric_only=True)

    matrice_corr.to_csv(OUTPUT_CSV, encoding="utf-8-sig")
    print(f"Matrice complète écrite : {OUTPUT_CSV}")

    corr_cible = (
        matrice_corr["consommation_mw"]
        .drop("consommation_mw")
        .sort_values(key=lambda s: s.abs(), ascending=False)
    )
    print("\n--- Corrélation avec consommation_mw (triée par force) ---")
    print(corr_cible.to_string(float_format=lambda x: f"{x:.3f}"))

    plt.figure(figsize=(16, 14))
    sns.heatmap(
        matrice_corr,
        cmap="coolwarm",
        center=0,
        vmin=-1, vmax=1,
        square=True,
        linewidths=0.5,
        annot=False,
    )
    plt.title("Matrice de corrélation - variables enrichies (lags, moyennes mobiles, cyclique) et consommation")
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=150)
    print(f"\nHeatmap écrite : {OUTPUT_PNG}")


if __name__ == "__main__":
    main()