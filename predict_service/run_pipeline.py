"""
Orchestrateur du pipeline de prédiction : crée le dossier de sortie s'il
n'existe pas encore, puis exécute les scripts du pipeline un par un, dans
l'ordre, en attendant que chacun se termine avant de lancer le suivant.

Principe :
  - subprocess.run() est BLOQUANT : il attend la fin du script lancé avant
    de rendre la main, donc les étapes s'enchaînent naturellement dans
    l'ordre de la liste SCRIPTS_A_EXECUTER, jamais en parallèle.
  - sys.executable garantit qu'on utilise le même interpréteur Python
    (et donc le même environnement/venv) que celui qui lance ce script.
  - Si une étape échoue (code de retour != 0), le pipeline s'arrête
    immédiatement : ça évite d'exécuter une étape suivante sur des
    données absentes ou périmées produites par une étape en échec.

Pour adapter à un autre pipeline : modifie DOSSIERS_A_CREER et
SCRIPTS_A_EXECUTER ci-dessous.
"""

import subprocess
import sys
from pathlib import Path

# Fichier "marqueur" de la racine du projet : tous les scripts du pipeline
# (feature_engineering.py, etc.) utilisent des chemins relatifs comme
# "base_analytique.duckdb" ou "predict_service/predictions/...", donc ils
# doivent impérativement être lancés avec cette racine comme dossier de
# travail (cwd) — peu importe où ce script d'orchestration lui-même est
# rangé (à la racine, dans predict_service/, ailleurs...). C'est ce qui a
# causé l'échec précédent : ce script étant maintenant dans predict_service/,
# RACINE valait predict_service/ au lieu de la racine EnergIA, et
# feature_engineering.py cherchait alors base_analytique.duckdb au mauvais
# endroit (predict_service/base_analytique.duckdb au lieu de la racine).
MARQUEUR_RACINE = "base_analytique.duckdb"


def trouver_racine_projet(depart: Path) -> Path:
    """Remonte les dossiers parents depuis `depart` jusqu'à trouver celui
    contenant MARQUEUR_RACINE. Rend ce script indépendant de l'endroit où
    il est lui-même placé (racine du projet ou sous-dossier)."""
    candidat = depart
    while True:
        if (candidat / MARQUEUR_RACINE).exists():
            return candidat
        parent = candidat.parent
        if parent == candidat:
            raise FileNotFoundError(
                f"Impossible de trouver {MARQUEUR_RACINE} en remontant depuis "
                f"{depart} : place ce script quelque part sous la racine du "
                f"projet EnergIA (là où se trouve {MARQUEUR_RACINE})."
            )
        candidat = parent


RACINE = trouver_racine_projet(Path(__file__).resolve().parent)

# Dossier(s) à créer s'ils n'existent pas avant de lancer le pipeline
# (chemins relatifs à la racine RÉELLE du projet, retrouvée ci-dessus)
DOSSIERS_A_CREER = [
    RACINE / "predict_service" / "predictions",
]

# Scripts à exécuter, dans l'ordre, chemins relatifs à la racine du projet
SCRIPTS_A_EXECUTER = [
    "predict_service/feature_engineering.py",
    "predict_service/correl.py",
    "predict_service/split_train_test.py",
    "predict_service/train_random_forest.py",
    "predict_service/prediction_future.py",
]


def creer_dossiers():
    for dossier in DOSSIERS_A_CREER:
        if dossier.exists():
            print(f"Dossier déjà présent : {dossier}")
        else:
            dossier.mkdir(parents=True, exist_ok=True)
            print(f"Dossier créé : {dossier}")


def executer_script(chemin_relatif: str):
    chemin = RACINE / chemin_relatif
    if not chemin.exists():
        raise FileNotFoundError(f"Script introuvable : {chemin}")

    print(f"\n{'=' * 70}")
    print(f"Lancement : {chemin_relatif}")
    print(f"{'=' * 70}")

    resultat = subprocess.run(
        [sys.executable, str(chemin)],
        cwd=RACINE,  # les scripts utilisent des chemins relatifs à la racine du projet
    )

    if resultat.returncode != 0:
        raise RuntimeError(
            f"{chemin_relatif} a échoué (code de retour {resultat.returncode}) : "
            f"pipeline interrompu, les étapes suivantes ne sont pas lancées."
        )

    print(f"Terminé : {chemin_relatif}")


def main():
    print(f"Racine du projet détectée : {RACINE}")

    print("\nPréparation des dossiers...")
    creer_dossiers()

    print(f"\n{len(SCRIPTS_A_EXECUTER)} script(s) à exécuter dans l'ordre.")
    for script in SCRIPTS_A_EXECUTER:
        executer_script(script)

    print(f"\n{'=' * 70}")
    print("Pipeline terminé avec succès.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
