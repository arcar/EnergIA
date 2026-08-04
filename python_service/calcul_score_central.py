import os 
import json

parent = os.path.dirname(os.path.abspath(__file__))
fichier_data = os.path.join(parent, "data", "parc-nucleaire-prescriptif-france.json")

def extract_data():
    with open(fichier_data, "r", encoding="utf-8") as json_file:
        return json.load(json_file)
        
def distance_km(edges):
    return edges["geodesic_distance_km"]

def loss_percent(edges):
    return edges["estimated_loss_percent"]


def final_load_ratio(centrale, scenario):
    return (centrale["simulation"]["initial_output_mw"] + scenario["additional_demand_mw"]) / centrale["simulation"]["soft_upper_bound_mw"]

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
    if (centrale["region_id"] == scenario["region_id"]):
        return 50
    else:
        return 0
    


def donnees_scores(donnees, scenario):
    resultats = []

    for edges in donnees["plant_edges"]:
        resultats.append({
            "distance_km": distance_km(edges),
            "loss_percent": loss_percent(edges)
        })

    for centrale in donnees["plants"]:
        resultats.append({
            "id": centrale["id"],
            "final_load_ratio" : final_load_ratio(centrale, scenario),
            "technical_penalty" : technical_penalty(centrale),
            "regional_priority_bonus" : regional_priority_bonus_if_local(centrale, scenario)

        })

    return resultats