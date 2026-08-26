import os 
import json
import numpy as np

parent = os.path.dirname(os.path.abspath(__file__))
parc_nucleaire_data = os.path.join(parent, "data", "parc-nucleaire-prescriptif-france.json")
parametres_temporels_nucleaire_data = os.path.join(parent, "data", "energia-parametres-temporels-nucleaire.json")
reference_consomation_data = os.path.join(parent, "data", "energia-journee-reference-consommation.json")
parc_non_pilotable_data = os.path.join(parent, "data", "energia-production-non-pilotable.json")

with open(reference_consomation_data, "r", encoding="utf-8") as json_file:
    data = json.load(json_file)

with open(parc_non_pilotable_data, "r", encoding="utf-8") as fichier:
    non_pilotable_data = json.load(fichier)

with open(parametres_temporels_nucleaire_data, "r", encoding="utf-8") as json_file:
    params_temporels = json.load(json_file)


prod_nucleaire_france = 0
min_prod_france = 0

for max in params_temporels["plants"]:
    prod_nucleaire_france += max["maximum_power_mw"]
    min_prod_france += max["minimum_operating_power_mw"]


demande_residuelle = (np.array(data["national_total_consumption_mw"]) - np.array(non_pilotable_data["national_total_production_mw"]["solar_plus_wind"])).tolist()

#print (demande_residuelle)

pourc_prod = (np.array(demande_residuelle) / np.array(prod_nucleaire_france)).tolist()

prod_reelle = []
centrales_deficit = []
centrales_excedent = []

for index, centrale in enumerate(params_temporels["plants"]):

    for heure, pct in zip(
        non_pilotable_data["timestamps"],
        pourc_prod
    ):

        prod_reelle.append({
            "plant_id": centrale["plant_id"],
            "heure": heure,
            "production": centrale["maximum_power_mw"] * pct
        })

        if prod_reelle[index]["production"] < centrale["minimum_operating_power_mw"]:
            augmentation_atteindre_seuil = centrale["minimum_operating_power_mw"] - prod_reelle[index]["production"]
            prod_reelle[index]["production"] += augmentation_atteindre_seuil
            centrale_deficit = prod_reelle[index]
            centrale_deficit["augmentation_atteindre_seuil"] = augmentation_atteindre_seuil
            centrales_deficit.append(centrale_deficit)
        elif prod_reelle[index]["production"] > centrale["minimum_operating_power_mw"]:
            dimunition_atteindre_seuil = centrale["maximum_power_mw"] -  prod_reelle[index]["production"]
            prod_reelle[index]["production"] -= dimunition_atteindre_seuil
            centrale_excedent = prod_reelle[index]
            centrale_excedent["dimunition_atteindre_seuil"] = dimunition_atteindre_seuil
            centrales_excedent.append(centrale_excedent)


print(centrales_excedent)




