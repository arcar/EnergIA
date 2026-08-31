import os 
import json

parent = os.path.dirname(os.path.abspath(__file__))
parc_nucleaire_data = os.path.join(parent, "data", "parc-nucleaire-prescriptif-france.json")
parametres_temporels_nucleaire_data = os.path.join(parent, "data", "energia-parametres-temporels-nucleaire.json")
reference_consomation_data = os.path.join(parent, "data", "energia-journee-reference-consommation.json")

def extract_data():
    with open(parc_nucleaire_data, "r", encoding="utf-8") as json_file:
        return json.load(json_file)

def extract_production():
    with open(parametres_temporels_nucleaire_data, "r", encoding="utf-8") as donnees_production_centrales:
        return json.load(donnees_production_centrales)

def extract_consomation_temporels():
    with open(reference_consomation_data, "r", encoding="utf-8") as donnees_consomation_regionale:
            return json.load(donnees_consomation_regionale)

def find_centrale(plants, destination):
    for centrale in plants:
        if centrale["plant_id"] == destination:
            return centrale
    return None

def find_centrale_reacteurs(plants, destination):
    for centrale in plants:
        if centrale["id"] == destination:
            return centrale
    return None


def final_load_ratio(soft_upper_bound, production_actuelle, puissance_affectee):
    return (production_actuelle + puissance_affectee) / soft_upper_bound

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




def donnees_scores(source_plant, destination, distance_km, total_loss_percent, centrale, demande_residuelle, max_transfer_mw, etat_precedent, facteur_reserve, centrale_reacteurs, production_debut_heure):
    production_actuelle = etat_precedent[centrale["plant_id"]]
    soft_upper_bound = centrale["maximum_power_mw"] * facteur_reserve

    rampe_deja_utilisee = production_actuelle - production_debut_heure[centrale["plant_id"]]
    marge_rampe_restante = centrale["max_ramp_up_mw_per_15_min"] - rampe_deja_utilisee

    marge_technique = soft_upper_bound - production_actuelle
    puissance_disponible = min(marge_technique, marge_rampe_restante)

    return {
        "source_central": source_plant,
        "destination_centrale": destination,
        "distance_km": distance_km,
        "loss_percent": total_loss_percent,
        "final_load_ratio": final_load_ratio(soft_upper_bound, production_actuelle, min(puissance_disponible, max_transfer_mw)),
        "technical_penalty": technical_penalty(centrale_reacteurs),
        "max_transfer_mw": max_transfer_mw,
        "puissance_disponible": puissance_disponible,
    }

def calcul_scores(source_plant, destination, distance_km, total_loss_percent, max_transfer_mw, demande_residuelle, etat_precedent, facteur_reserve, centrale, centrale_reacteurs, production_debut_heure):
    if centrale is None:
        print("Centrale introuvable :", destination)
        return None

    distance_weight = 1.0
    loss_weight = 45.0
    saturation_weight = 900.0
    technical_penalty_weight = 200.0
    resultats = donnees_scores(source_plant, destination, distance_km, total_loss_percent, centrale, demande_residuelle, max_transfer_mw, etat_precedent, facteur_reserve, centrale_reacteurs, production_debut_heure)

    resultats["score_candidat"] = (
        resultats["distance_km"] * distance_weight
        + resultats["loss_percent"] * loss_weight
        + pow(resultats["final_load_ratio"], 4) * saturation_weight
        + resultats["technical_penalty"] * technical_penalty_weight
    )

    return resultats
    
