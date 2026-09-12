"""
Récupère, pour chaque région française, plusieurs indicateurs DPE depuis
l'API data-fair de l'ADEME (dataset dpe03existant) et exporte le tout en
CSV / Excel.

Principe : au lieu de boucler région par région, on agrège directement sur
le champ `code_region_ban` (field=code_region_ban) : un seul appel renvoie
alors les ~19 régions d'un coup. Seul le filtre `qs` change selon
l'indicateur voulu (étiquette DPE, chauffage électrique, climatisation...).

Dépendances : requests, pandas, openpyxl
    pip install requests pandas openpyxl
"""

import requests
import pandas as pd

BASE_URL = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/values_agg"
OUTPUT_PATH_dpe = "etl_analytique/data/dpe.csv"

# Correspondance code région INSEE -> nom (utilisée pour l'affichage)
REGION_NAMES = {
    "11": "Île-de-France",
    "24": "Centre-Val de Loire",
    "27": "Bourgogne-Franche-Comté",
    "28": "Normandie",
    "32": "Hauts-de-France",
    "44": "Grand Est",
    "52": "Pays de la Loire",
    "53": "Bretagne",
    "75": "Nouvelle-Aquitaine",
    "76": "Occitanie",
    "84": "Auvergne-Rhône-Alpes",
    "93": "Provence-Alpes-Côte d'Azur",
    "94": "Corse",
   }

# Un indicateur = un nom de colonne + le filtre "qs" à appliquer.
# qs=None -> pas de filtre (total par région, toutes valeurs confondues)
INDICATEURS = {
    "total_dpe": None,
    "A": 'etiquette_dpe:A',
    "B": 'etiquette_dpe:B',
    "C": 'etiquette_dpe:C',
    "D": 'etiquette_dpe:D',
    "E": 'etiquette_dpe:E',
    "F": 'etiquette_dpe:F',
    "G": 'etiquette_dpe:G',
    "chauffage_electrique": 'type_energie_principale_chauffage:"Électricité"',
    "climatisation": 'conso_refroidissement_annuel:>0',
}


def fetch_region_counts(qs: str | None, agg_size: int = 30) -> dict[str, int]:
    """Appelle values_agg(field=code_region_ban) avec un filtre qs donné et
    renvoie un dict {code_region: total}."""
    params = {
        "field": "code_region_ban",
        "metric": "count",
        "agg_size": agg_size,
    }
    if qs:
        params["qs"] = qs

    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return {agg["value"]: agg["total"] for agg in data["aggs"]}, data["total"]


def main():
    columns: dict[str, dict[str, int]] = {}
    national_totals: dict[str, int] = {}

    for col_name, qs in INDICATEURS.items():
        region_counts, national_total = fetch_region_counts(qs)
        columns[col_name] = region_counts
        national_totals[col_name] = national_total
        print(f"{col_name}: OK ({len(region_counts)} régions, total national={national_total})")

    # Construction du DataFrame : une ligne par région
    df = pd.DataFrame(columns)
    df.index.name = "code_region"
    df.insert(0, "region", df.index.map(REGION_NAMES))
    df = df.fillna(0)
    for col in INDICATEURS:
        df[col] = df[col].astype(int)

    df = df.sort_values("total_dpe", ascending=False)

    # Ligne de contrôle : écart entre somme des régions et total national
    # (DPE sans code région géolocalisé)
    ecart = {col: national_totals[col] - df[col].sum() for col in INDICATEURS}

    print("\n--- Écart total national vs somme des régions (non géolocalisés) ---")
    for col, val in ecart.items():
        print(f"{col}: {val}")

    df.to_csv(OUTPUT_PATH_dpe, encoding="utf-8-sig")
    

    print("\nFichiers écrits : dpe_par_region.csv")


if __name__ == "__main__":
    main()
