import os 
import json

parent = os.path.dirname(os.path.abspath(__file__))
fichier_data = os.path.join(parent, "data", "parc-nucleaire-prescriptif-france.json")

def extract_data():
    with open(fichier_data, "r", encoding="utf-8") as json_file:
        return json.load(json_file)

def find_centrale(plants, destination):
    for centrale in plants:
        if (centrale["id"] == destination):
            return centrale
    return None


def final_load_ratio(centrale, augmentation):
    initial_output = centrale["simulation"]["initial_output_mw"]
    soft_upper_bound = centrale["simulation"]["soft_upper_bound_mw"]
    return ((initial_output + augmentation) / soft_upper_bound)

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



def donnees_scores( source_plant, destination, distance_km, total_loss_percent, centrale, demande_residuelle, max_transfer_mw):

    return {
            "source_central": source_plant,
            "destination_centrale": destination,
            "distance_km": distance_km,
            "loss_percent": total_loss_percent,
            "final_load_ratio": final_load_ratio(centrale, demande_residuelle),
            "technical_penalty": technical_penalty(centrale),
            "max_transfer": max_transfer_mw
        }

def calcul_scores(source_plant, destination, distance_km, total_loss_percent, max_transfer_mw, demande_residuelle):
    donnees = extract_data()
    centrale = find_centrale(donnees["plants"], destination)
    distance_weight = 1.0
    loss_weight = 45.0
    saturation_weight = 900.0
    technical_penalty_weight = 200.0 
    resultats = donnees_scores(source_plant, destination, distance_km, total_loss_percent, centrale, demande_residuelle , max_transfer_mw)
    
    
    resultats["score_candidat"] = (
            resultats["distance_km"] * distance_weight + resultats["loss_percent"] *loss_weight + pow(resultats["final_load_ratio"], 4) * saturation_weight + resultats["technical_penalty"] * technical_penalty_weight
    )


    return resultats

    
