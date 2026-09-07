import os
import json

PARENT = os.path.dirname(os.path.abspath(__file__))

PARC_NUCLEAIRE_DATA = os.path.join(PARENT, "data", "parc-nucleaire-prescriptif-france.json")

PARAMETRES_TEMPORELS_NUCLEAIRE_DATA = os.path.join(PARENT, "data", "energia-parametres-temporels-nucleaire.json")

REFERENCE_CONSOMMATION_DATA = os.path.join(PARENT, "data", "energia-journee-reference-consommation.json")

PARC_NON_PILOTABLE_DATA = os.path.join(PARENT, "data", "energia-production-non-pilotable.json")

def charger_json(chemin):
    with open(chemin, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def charger_donnees():
    return {
        "parc_nucleaire": charger_json(PARC_NUCLEAIRE_DATA),
        "params_temporels": charger_json(PARAMETRES_TEMPORELS_NUCLEAIRE_DATA),
        "consommation": charger_json(REFERENCE_CONSOMMATION_DATA),
        "non_pilotable": charger_json(PARC_NON_PILOTABLE_DATA),
    }