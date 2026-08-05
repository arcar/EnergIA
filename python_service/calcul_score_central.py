import os 
import json

parent = os.path.dirname(os.path.abspath(__file__))
fichier_data = os.path.join(parent, "data", "parc-nucleaire-prescriptif-france.json")

def extract_data():
    with open(fichier_data, "r", encoding="utf-8") as json_file:
        return json.load(json_file)

def find_centrale(plants, centrale_id):
    for centrale in plants:
        if (centrale["id"] == centrale_id):
            return centrale
    return None


def distance_km(edges):
    return edges["geodesic_distance_km"]

def loss_percent(edges):
    return edges["estimated_loss_percent"]


def final_load_ratio(centrale, scenario):
    initial_output = centrale["simulation"]["initial_output_mw"]
    soft_upper_bound = centrale["simulation"]["soft_upper_bound_mw"]
    transfered_production_mw = scenario["additional_demand_mw"]
    return ((initial_output + transfered_production_mw) / soft_upper_bound)

def technical_penalty(centrale):
    penalty = 0
    for reactor in centrale["reactors"]:
        if (reactor["status"] == "in_operation"):
            penalty += 0
        elif (reactor["status"] == "maintenance"):
            penalty += 10
        else:
            penalty += 100
    return penalty

def regional_priority_bonus_if_local(centrale, scenario):
    if (centrale["location"]["region_id"] == scenario["region_id"]):
        return -250
    else:
        return 0
    


def donnees_scores(donnees, scenario):
    resultats = []

    for edges in donnees["plant_edges"]:
        centrale = find_centrale(donnees["plants"], edges["from"])

        if centrale is None:
            continue

        resultats.append({
            "from": edges["from"],
            "to": edges["to"],
            "distance_km": distance_km(edges),
            "loss_percent": loss_percent(edges),
            "final_load_ratio": final_load_ratio(centrale, scenario),
            "technical_penalty": technical_penalty(centrale),
            "regional_priority_bonus": regional_priority_bonus_if_local(centrale, scenario)
        })
    return resultats

def calcul_scores():
    donnees = extract_data()

    distance_weight = 1.0
    loss_weight = 45.0
    saturation_weight = 900.0
    technical_penalty_weight = 200.0 
    scores = []

    for scenario in donnees["example_scenarios"]:

        resultats = donnees_scores(donnees, scenario)
        for resultat in resultats:
            resultat["score_candidat"] = (
                resultat["distance_km"] * distance_weight + resultat["loss_percent"] *loss_weight + pow(resultat["final_load_ratio"], 4) * saturation_weight + resultat["technical_penalty"] * technical_penalty_weight + resultat["regional_priority_bonus"]
            )
            scores.append(resultat)
        
    return scores

    
