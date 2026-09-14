import requests
import pandas as pd

BASE_URL = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/values_agg"
OUTPUT_PATH_dpe = "etl_analytique/data/dpe.csv"
OUTPUT_PATH_dpe_annee = "etl_analytique/data/dpe_par_annee.csv"

# Régions à exclure de l'export (DOM/territoires peu peuplés dans ce jeu de données)
REGIONS_EXCLUES = ["00", "01", "02", "03", "04", "06"]

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

# Sous-ensemble des indicateurs que l'on veut aussi ventiler par année
INDICATEURS_ANNUELS = ["total_dpe", "chauffage_electrique", "climatisation"]


def fetch_region_counts(qs: str | None, agg_size: int = 30) -> tuple[dict[str, int], int]:
    """Appelle values_agg(field=code_region_ban) avec un filtre qs donné et
    renvoie (dict {code_region: total}, total_national)."""
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


def fetch_years() -> list[int]:
    """Découvre les années présentes dans date_etablissement_dpe."""
    params = {
        "field": "date_etablissement_dpe",
        "metric": "count",
        "interval": "year",
        "agg_size": 50,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # chaque "value" est une date du type "2023-01-01"
    return sorted(int(agg["value"][:4]) for agg in data["aggs"])


def combine_qs(year: int, base_qs: str | None) -> str:
    """Combine un filtre qs existant avec une restriction sur l'année."""
    date_filter = f"date_etablissement_dpe:[{year}-01-01 TO {year}-12-31]"
    if base_qs:
        return f"{date_filter} AND {base_qs}"
    return date_filter


def build_table_region() -> pd.DataFrame:
    """Table région : un indicateur = une colonne, cumul toutes années confondues."""
    columns: dict[str, dict[str, int]] = {}
    national_totals: dict[str, int] = {}

    for col_name, qs in INDICATEURS.items():
        region_counts, national_total = fetch_region_counts(qs)
        columns[col_name] = region_counts
        national_totals[col_name] = national_total
        print(f"[région] {col_name}: OK ({len(region_counts)} régions, total national={national_total})")

    df = pd.DataFrame(columns)
    df.index.name = "code_region"
    df.insert(0, "region", df.index.map(REGION_NAMES))
    df = df.fillna(0)
    for col in INDICATEURS:
        df[col] = df[col].astype(int)

    df = df.sort_values("total_dpe", ascending=False)

    ecart = {col: national_totals[col] - df[col].sum() for col in INDICATEURS}
    print("\n--- Écart total national vs somme des régions (non géolocalisés) ---")
    for col, val in ecart.items():
        print(f"{col}: {val}")

    df = df.drop(index=[c for c in REGIONS_EXCLUES if c in df.index])
    return df


def build_table_region_annee() -> pd.DataFrame:
    """Table région x année pour les indicateurs listés dans INDICATEURS_ANNUELS."""
    years = fetch_years()
    print(f"\nAnnées détectées : {years}")

    per_indicateur_par_annee: dict[str, dict[int, dict[str, int]]] = {}

    for col_name in INDICATEURS_ANNUELS:
        base_qs = INDICATEURS[col_name]
        per_indicateur_par_annee[col_name] = {}
        for year in years:
            qs = combine_qs(year, base_qs)
            region_counts, national_total = fetch_region_counts(qs)
            per_indicateur_par_annee[col_name][year] = region_counts
            print(f"[année] {col_name} {year}: OK ({len(region_counts)} régions, total national={national_total})")

    # Format long : une ligne par (code_region, annee)
    rows = []
    for year in years:
        regions_presentes = set()
        for col_name in INDICATEURS_ANNUELS:
            regions_presentes |= set(per_indicateur_par_annee[col_name][year].keys())

        for code_region in regions_presentes:
            row = {"code_region": code_region, "annee": year}
            for col_name in INDICATEURS_ANNUELS:
                row[col_name] = per_indicateur_par_annee[col_name][year].get(code_region, 0)
            rows.append(row)

    df = pd.DataFrame(rows)
    df.insert(1, "region", df["code_region"].map(REGION_NAMES))
    df = df[~df["code_region"].isin(REGIONS_EXCLUES)]
    df = df.sort_values(["annee", "code_region"]).reset_index(drop=True)
    return df


def main():
    df_region_annee = build_table_region_annee()
    df_region_annee.to_csv(OUTPUT_PATH_dpe_annee, index=False, encoding="utf-8-sig")
    print(f"Fichier écrit : {OUTPUT_PATH_dpe_annee}")


if __name__ == "__main__":
    main()