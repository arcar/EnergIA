import os 
import json

parent = os.path.dirname(os.path.abspath(__file__))
parc_nucleaire_data = os.path.join(parent, "data", "parc-nucleaire-prescriptif-france.json")
parametres_temporels_nucleaire_data = os.path.join(parent, "data", "energia-parametres-temporels-nucleaire.json")
reference_consomation_data = os.path.join(parent, "data", "energia-journee-reference-consommation.json")

with open(reference_consomation_data, "r", encoding="utf-8") as json_file:
    data = json.load(json_file)


print (data["national_total_consumption_mw"])

with open(parametres_temporels_nucleaire_data, "r", encoding="utf-8") as json_file:
    params_temporels = json.load(json_file)

prod_nucleaire_france = 0

for max in params_temporels["plants"]:
    prod_nucleaire_france += max["maximum_power_mw"]

print(prod_nucleaire_france)




