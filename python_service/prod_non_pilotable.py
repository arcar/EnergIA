import os 
import json

parent = os.path.dirname(os.path.abspath(__file__))
parc_non_pilotable_data = os.path.join(parent, "data", "energia-production-non-pilotable.json")

with open(parc_non_pilotable_data, "r", encoding="utf-8") as fichier:
    data = json.load(fichier)

#-----------------------------------------
# SOLAIRE
#------------------------------------------

def get_capacite_solaire(region):
    for r in data["regions"]:
        if r["id"] == region:
            return r["synthetic_installed_capacity_mw"]["solar"]

    return None


def get_production_solaire(region, heure):
    for r in data["regions"]:
        if r["id"] == region:
            if heure in data["timestamps"]:
                index = data["timestamps"].index(heure)
                return r["production_mw"]["solar"][index]

    return None

# Calculer la puissance solaire disponible
def get_puissance_solaire_disponible(region, heure):
    capacite = get_capacite_solaire(region)
    production = get_production_solaire(region, heure)

    if capacite is None or production is None:
        return None

    return capacite - production


#Faire le calcul pour toutes les régions
def get_solaire_toutes_regions(heure):
    resultats = []

    for region in data["regions"]:
        region_id = region["id"]

        resultats.append({
            "region": region_id,
            "capacite_solaire": get_capacite_solaire(region_id),
            "production_solaire": get_production_solaire(region_id, heure),
            "puissance_solaire_disponible": get_puissance_solaire_disponible(
                region_id,
                heure
            )
        })

    return resultats









#-----------------------------------------
# EOLIEN
#------------------------------------------

# Calculer la capacité de production élolienne pour une région
def get_capacite_eolienne(region):
    for r in data["regions"]:
        if r["id"] == region:
            return r["synthetic_installed_capacity_mw"]["wind"]

    return None

# Récupérer la production élolienne pour une région à une heure donnée
def get_production_eolienne(region, heure):
    for r in data["regions"]:
        if r["id"] == region:
            if heure in data["timestamps"]:
                index = data["timestamps"].index(heure)
                return r["production_mw"]["wind"][index]

    return None

# Calculer la puissance eolienne disponible
def get_puissance_eolienne_disponible(region, heure):
    capacite = get_capacite_eolienne(region)
    production = get_production_eolienne(region, heure)

    if capacite is None or production is None:
        return None

    return capacite - production


# Faire le calcul pour toutes les régions
def get_eolien_toutes_regions(heure):
    resultats = []

    for region in data["regions"]:
        region_id = region["id"]

        resultats.append({
            "region": region_id,
            "capacite_eolienne": get_capacite_eolienne(region_id),
            "production_eolienne": get_production_eolienne(region_id, heure),
            "puissance_eolienne_disponible": get_puissance_eolienne_disponible(
                region_id,
                heure
            )
        })

    return resultats









#-----------------------------------------
# demande résiduelle
#------------------------------------------

# #récupérer la capacité eolienne d'une region
# print(get_capacite_eolienne("normandie"))

# #récupérer la prod eolienne d'une heure donnée
# print(get_production_eolienne("normandie", "12:00"))
# #résultat calcul disponibilité
# print(get_puissance_eolienne_disponible("normandie", "12:00"))

# resultats = get_eolien_toutes_regions("12:00")

# for resultat in resultats:
#     print(resultat)