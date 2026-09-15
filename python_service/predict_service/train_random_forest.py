"""
Étape 4 du pipeline de prédiction : entraînement d'un Random Forest pour
prédire consommation_mw, à un HORIZON choisi parmi 1h, 1j, 1semaine,
1mois, 1an.

Principe multi-horizon : le dataset (01_feature_engineering.py) contient
5 lags (lag_1h, lag_1j, lag_1semaine, lag_1mois, lag_1an). Selon l'horizon
choisi, seuls les lags D'AU MOINS cette durée sont des features valides —
les plus courts décrivent des instants entre le moment de la prédiction et
sa cible, donc pas encore connus en situation réelle. Par exemple, pour
HORIZON = "1mois" : lag_1mois et lag_1an sont utilisables, lag_1h/1j/1semaine
sont exclus des features.

Changer uniquement HORIZON (juste en dessous) et relancer ce script suffit
pour obtenir un modèle adapté à un autre horizon de prédiction.

Autres variables volontairement EXCLUES des features (X), quel que soit
l'horizon :
  - id_region, id_temps, date, region : identifiants / texte, remplacés par
    un one-hot sur "region" (cardinalité faible, adapté au one-hot) et par
    les variables temporelles déjà encodées.
  - production_nucleaire_mw, production_eolienne_mw, production_solaire_mw :
    mesurées AU MÊME instant que consommation_mw (le réseau équilibre
    production et consommation en temps réel) : les inclure serait une
    fuite de données, quel que soit l'horizon.

Entrées : predict_service/predictions/train.csv, test.csv (sortie de 03_split_train_test.py)
Sorties :
    predict_service/predictions/modele_random_forest_{HORIZON}.joblib
    predict_service/predictions/feature_importances_{HORIZON}.csv
    predict_service/predictions/predictions_vs_reel_{HORIZON}.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ---------------------------------------------------------------------
# Horizon de prédiction voulu : "1h", "1j", "1semaine", "1mois" ou "1an"
HORIZON = "1an"
# ---------------------------------------------------------------------

TRAIN_CSV = "python_service/predict_service/predictions/train.csv"
TEST_CSV = "python_service/predict_service/predictions/test.csv"

CIBLE = "consommation_mw"

# Ordre du plus court au plus long : détermine, pour un horizon donné,
# quels lags restent valides (ceux à partir de sa position dans la liste)
ORDRE_HORIZONS = ["1h", "1j", "1semaine", "1mois", "1an"]
LAG_PAR_HORIZON = {
    "1h": "lag_1h",
    "1j": "lag_1j",
    "1semaine": "lag_1semaine",
    "1mois": "lag_1mois",
    "1an": "lag_1an",
}

COLONNES_A_EXCLURE_FIXE = [
    "id_region", "id_temps", "date", "region",
    "production_nucleaire_mw", "production_eolienne_mw", "production_solaire_mw",
    CIBLE,
]

COLONNES_BOOL = [
    "weekend", "printemps", "ete", "automne", "hiver",
    "vacances_zone_a", "vacances_zone_b", "vacances_zone_c",
]


def lags_invalides_pour_horizon(horizon: str) -> list[str]:
    """Renvoie les colonnes de lag trop courtes pour être utilisées
    à l'horizon demandé (donc à exclure des features)."""
    if horizon not in ORDRE_HORIZONS:
        raise ValueError(f"HORIZON invalide : {horizon!r}. Choix possibles : {ORDRE_HORIZONS}")
    index_horizon = ORDRE_HORIZONS.index(horizon)
    horizons_trop_courts = ORDRE_HORIZONS[:index_horizon]
    return [LAG_PAR_HORIZON[h] for h in horizons_trop_courts]


def prepare_features(df: pd.DataFrame, colonnes_a_exclure: list[str]) -> pd.DataFrame:
    X = df.drop(columns=[c for c in colonnes_a_exclure if c in df.columns])

    for col in COLONNES_BOOL:
        if col in X.columns:
            X[col] = X[col].astype(int)

    if "zone_scolaire" in X.columns:
        X = pd.get_dummies(X, columns=["zone_scolaire"], prefix="zone")
    if "region" in df.columns:
        X["region"] = df["region"]
        X = pd.get_dummies(X, columns=["region"], prefix="region")

    for col in X.columns:
        if X[col].dtype == bool:
            X[col] = X[col].astype(int)

    return X


def main():
    lags_a_exclure = lags_invalides_pour_horizon(HORIZON)
    colonnes_a_exclure = COLONNES_A_EXCLURE_FIXE + lags_a_exclure
    lag_baseline = LAG_PAR_HORIZON[HORIZON]

    print(f"Horizon choisi : {HORIZON}")
    print(f"Lags exclus des features (trop courts pour cet horizon) : {lags_a_exclure or 'aucun'}")
    print(f"Baseline de comparaison : {lag_baseline}")

    model_path = f"python_service/predict_service/predictions/modele_random_forest_{HORIZON}.joblib"
    importances_csv = f"python_service/predict_service/predictions/feature_importances_{HORIZON}.csv"
    plot_path = f"python_service/predict_service/predictions/predictions_vs_reel_{HORIZON}.png"

    print("\nChargement train/test...")
    train = pd.read_csv(TRAIN_CSV)
    test = pd.read_csv(TEST_CSV)
    print(f"Train : {len(train):,} lignes | Test : {len(test):,} lignes")

    y_train = train[CIBLE]
    y_test = test[CIBLE]

    X_train = prepare_features(train, colonnes_a_exclure)
    X_test = prepare_features(test, colonnes_a_exclure)

    # Réalignement des colonnes one-hot : le test doit avoir exactement les
    # mêmes colonnes que le train, dans le même ordre (sinon RandomForest
    # interprète les colonnes par position et non par nom)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

    print(f"\n{X_train.shape[1]} features utilisées :")
    print(list(X_train.columns))

    print("\nEntraînement du Random Forest...")
    modele = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    modele.fit(X_train, y_train)

    y_pred = modele.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"\n--- Performance du Random Forest sur le test (horizon {HORIZON}) ---")
    print(f"MAE  : {mae:,.1f} MW")
    print(f"RMSE : {rmse:,.1f} MW")
    print(f"R²   : {r2:.3f}")

    # Baseline de comparaison : le lag le plus court encore valide à cet
    # horizon (la prévision naïve la plus compétitive possible sans fuite).
    # Un modèle utile doit faire mieux que ça.
    if lag_baseline in test.columns:
        y_baseline = test[lag_baseline]
        mae_base = mean_absolute_error(y_test, y_baseline)
        rmse_base = np.sqrt(mean_squared_error(y_test, y_baseline))
        r2_base = r2_score(y_test, y_baseline)
        print(f"\n--- Baseline de comparaison (persistance = {lag_baseline}) ---")
        print(f"MAE  : {mae_base:,.1f} MW")
        print(f"RMSE : {rmse_base:,.1f} MW")
        print(f"R²   : {r2_base:.3f}")

    importances = (
        pd.Series(modele.feature_importances_, index=X_train.columns)
        .sort_values(ascending=False)
    )
    importances.to_csv(importances_csv, header=["importance"], encoding="utf-8-sig")
    print(f"\n--- Importance des variables (top 15) ---")
    print(importances.head(15).to_string(float_format=lambda x: f"{x:.3f}"))
    print(f"\nImportances complètes écrites : {importances_csv}")

    plt.figure(figsize=(14, 6))
    n_points = min(len(y_test), 500)
    plt.plot(y_test.values[:n_points], label="Consommation réelle", linewidth=1)
    plt.plot(y_pred[:n_points], label=f"Consommation prédite (Random Forest, horizon {HORIZON})", linewidth=1)
    plt.xlabel("Index (ordre chronologique, test)")
    plt.ylabel("Consommation (MW)")
    plt.title(f"Prédictions vs réel — horizon {HORIZON} — premiers {n_points} points du test")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    print(f"Graphique écrit : {plot_path}")

    joblib.dump({"modele": modele, "colonnes": list(X_train.columns), "horizon": HORIZON}, model_path)
    print(f"\nModèle sauvegardé : {model_path}")


if __name__ == "__main__":
    main()