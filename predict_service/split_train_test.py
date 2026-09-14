"""
Étape 3 du pipeline de prédiction : split train/test par ANNÉE COMPLÈTE
(adapté à un horizon de prédiction d'au moins un an).

Principe : le test doit être une année entière, jamais vue dans le train,
et strictement postérieure à toutes les années du train — c'est la seule
façon d'évaluer honnêtement un modèle censé prédire un an à l'avance.

  - test  = la dernière année COMPLÈTE présente dans les données
  - train = toutes les années strictement antérieures au test
  - toute année postérieure au test (une année en cours, partielle) est
    écartée de cet entraînement/évaluation : elle sera utilisable plus
    tard comme vrai jeu de prédiction "futur" une fois complète.

On détecte automatiquement la dernière année comme "en cours / partielle"
si elle ne couvre pas 12 mois pleins dans les données, et on prend alors
l'année précédente comme année de test.

Entrée  : etl_analytique/predictions/dataset_features.csv (sortie de 01_feature_engineering.py)
Sorties : etl_analytique/predictions/train.csv
          etl_analytique/predictions/test.csv
"""

import pandas as pd

INPUT_CSV = "predict_service/predictions/dataset_features.csv"
OUTPUT_TRAIN = "predict_service/predictions/train.csv"
OUTPUT_TEST = "predict_service/predictions/test.csv"


def annee_est_complete(df: pd.DataFrame, annee: int) -> bool:
    """Une année est considérée complète si les données couvrent bien
    les 12 mois de cette année (au moins une ligne par mois)."""
    mois_presents = df.loc[df["year"] == annee, "month"].unique()
    return len(mois_presents) >= 12


def main():
    print(f"Lecture de {INPUT_CSV} ...")
    df = pd.read_csv(INPUT_CSV, parse_dates=["date"])
    print(f"{len(df):,} lignes chargées.")

    annees = sorted(df["year"].unique())
    print(f"Années présentes : {annees}")

    derniere_annee = annees[-1]
    if not annee_est_complete(df, derniere_annee):
        print(f"L'année {derniere_annee} est incomplète dans les données "
              f"(mois manquants) -> écartée du train/test.")
        annees_utilisables = [a for a in annees if a != derniere_annee]
    else:
        annees_utilisables = annees

    if len(annees_utilisables) < 2:
        raise ValueError(
            "Pas assez d'années complètes pour un split train/test à horizon "
            "1 an (il en faut au moins 2 : au moins une pour le train, une "
            "pour le test)."
        )

    test_year = annees_utilisables[-1]
    train_years = [a for a in annees_utilisables if a < test_year]

    train = df[df["year"].isin(train_years)].copy()
    test = df[df["year"] == test_year].copy()

    print(f"\nAnnée de test : {test_year}")
    print(f"Années de train : {train_years}")

    print(f"\n--- Train ---")
    print(f"{len(train):,} lignes")
    print(f"Période : {train['date'].min().date()} -> {train['date'].max().date()}")

    print(f"\n--- Test ---")
    print(f"{len(test):,} lignes")
    print(f"Période : {test['date'].min().date()} -> {test['date'].max().date()}")

    regions_train = set(train["id_region"].unique())
    regions_test = set(test["id_region"].unique())
    regions_manquantes = regions_test - regions_train
    if regions_manquantes:
        print(f"\n/!\\ Attention : régions présentes dans le test mais absentes "
              f"du train : {regions_manquantes}")
    else:
        print(f"\nOK : les {len(regions_train)} régions du train couvrent bien "
              f"toutes les régions du test.")

    train.to_csv(OUTPUT_TRAIN, index=False, encoding="utf-8-sig")
    test.to_csv(OUTPUT_TEST, index=False, encoding="utf-8-sig")
    print(f"\nFichiers écrits :\n  {OUTPUT_TRAIN}\n  {OUTPUT_TEST}")


if __name__ == "__main__":
    main()