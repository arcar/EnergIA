from extraction_json import charger_donnees
from pathlib import Path
import duckdb


BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "base_analytique.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)
result = conn.execute("SELECT * FROM dim_temps").fetchall()
data = charger_donnees()


def donnees_centrales_30_min():
    new_donnees_centrales_30_min = []
    for centrale in data["params_temporels"]["plants"]:
        rampe_up_ajustee_30_min = centrale["max_ramp_up_mw_per_15_min"] * 2
        rampe_down_ajustee_30_min = centrale["max_ramp_down_mw_per_15_min"] * 2
        new_donnees_centrales_30_min.append({
            "plant_id" : centrale["plant_id"],
            "rampe_up_ajustee_30_min" : rampe_up_ajustee_30_min,
            "rampe_down_ajustee_30_min" : rampe_down_ajustee_30_min,
            "initial_output_mw_at_23_30_previous_day" : centrale["initial_output_mw_at_23_45_previous_day"],
            "minimum_operating_power_mw" : centrale["minimum_operating_power_mw"],
            "maximum_power_mw" : centrale["maximum_power_mw"],
        })

    return new_donnees_centrales_30_min



def production_non_pilotables_regional_duckdb():
    con = duckdb.connect(str(DB_PATH), read_only=True)

    result = con.execute("""
        SELECT dr.region, dt.date, dt.heure, fe.production_eolienne_mw, fe.production_solaire_mw
        FROM dim_region AS dr
        JOIN fait_energie AS fe ON dr.id_region = fe.id_region
        JOIN dim_temps AS dt ON dt.id_temps = fe.id_temps
        ORDER BY dr.region, dt.date, dt.heure
    """)

    colonnes = [desc[0] for desc in result.description]
    lignes = [dict(zip(colonnes, ligne)) for ligne in result.fetchall()]

    production_par_region = {}

    for ligne in lignes:
        region_id = ligne["region"]

        if region_id not in production_par_region:
            production_par_region[region_id] = []

        production_par_region[region_id].append({
            "date": ligne["date"],
            "heure": ligne["heure"],
            "production_eolienne_mw": ligne["production_eolienne_mw"],
            "production_solaire_mw": ligne["production_solaire_mw"]
        })

    con.close()
    return production_par_region

resultat = production_non_pilotables_regional_duckdb()
for region, valeurs in resultat.items():
    print(region, "->", len(valeurs), "points, premières valeurs:", valeurs[:5])