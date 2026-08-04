import os 
import json

parent = os.path.dirname(os.path.abspath(__file__))
fichier_data = os.path.join(parent, "data", "parc-nucleaire-prescriptif-france.json")

def extract_data():
    with open(fichier_data, "r", encoding="utf-8") as json_file:
        return json.load(json_file)
        


def calcul_puissance_disponible(centrale):
    return centrale["simulation"]["soft_upper_bound_mw"] - centrale["simulation"]["initial_output_mw"]

def taux_saturation(centrale):
    return centrale["simulation"]["initial_load_ratio"]

def verifier_disponibilite(centrale):
    return centrale["simulation"]["available"]

def metriques_centrales(donnees):
    resultats = []

    for centrale in donnees["plants"]:
        resultats.append({
            "id": centrale["id"],
            "puissance_disponible": calcul_puissance_disponible(centrale),
            "taux_saturation": taux_saturation(centrale),
            "disponible": verifier_disponibilite(centrale)
        })

    return resultats