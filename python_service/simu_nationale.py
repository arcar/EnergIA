import os 
import json
import numpy as np

parent = os.path.dirname(os.path.abspath(__file__))
parc_nucleaire_data = os.path.join(parent, "data", "parc-nucleaire-prescriptif-france.json")
parametres_temporels_nucleaire_data = os.path.join(parent, "data", "energia-parametres-temporels-nucleaire.json")
reference_consomation_data = os.path.join(parent, "data", "energia-journee-reference-consommation.json")
parc_non_pilotable_data = os.path.join(parent, "data", "energia-production-non-pilotable.json")

# --------------------------------------------------------------------------------
# Fonction de chargement du fichier Json
# --------------------------------------------------------------------------------
def charger_json(chemin) :
    with open(chemin, "r", encoding="utf-8") as fichier:
        return json.load(fichier)

# --------------------------------------------------------------------------------
# Fonction d'enregistrement de la production des centrales nucléaires
# --------------------------------------------------------------------------------
def enregistrer_productions(centrales, heure, prod_reelle, etat_precedent):
    for centrale in centrales:
        prod_reelle.append({
            "plant_id": centrale["plant_id"],
            "heure": heure,
            "production": centrale["production"],
            "production_demandee": centrale["production_demandee"],
            "production_precedente": centrale["production_precedente"],
            "variation_mw": centrale["production"] - centrale["production_precedente"],
            "minimum_autorise": centrale["minimum"],
            "maximum_autorise": centrale["maximum"],
            "production_minimum_technique": centrale["minimum_technique"],
            "production_maximum_technique": centrale["maximum_technique"],
            "rampe_montee_maximale": centrale["rampe_montee"],
            "rampe_descente_maximale": centrale["rampe_descente"],
        })

        etat_precedent[centrale["plant_id"]] = centrale["production"]

# --------------------------------------------------------------------------------
# Fonction de calcul de la variale centrales_heure
# --------------------------------------------------------------------------------
def calculer_centrales_heure(centrale, pourcentage, etat_precedent):
    plant_id = centrale["plant_id"]

    production_demandee = (centrale["maximum_power_mw"] * pourcentage)

    production_precedente = etat_precedent[plant_id]

    # Limite imposée par la capacité de la centrale
    minimum_technique = centrale["minimum_operating_power_mw"]
    maximum_technique = centrale["maximum_power_mw"]
    
    # Limite imposée par la vitesse de montée et descente
    minimum_temporel = (production_precedente - centrale["max_ramp_down_mw_per_15_min"])
    maximum_temporel = (production_precedente + centrale["max_ramp_up_mw_per_15_min"])
    
    # Combinaison des limites techniques et temporelles pour obtenir la meilleure contrainte (technique ou temporelle)
    minimum_autorise = max(minimum_technique, minimum_temporel)
    maximum_autorise = min(maximum_technique, maximum_temporel)

    return {
        "plant_id": plant_id,
        "production": production_demandee,
        "production_demandee": production_demandee,
        "production_precedente": production_precedente,
        "minimum": minimum_autorise,
        "maximum": maximum_autorise,
        "minimum_technique": minimum_technique,
        "maximum_technique": maximum_technique,
        "rampe_montee": centrale["max_ramp_up_mw_per_15_min"],
        "rampe_descente": centrale["max_ramp_down_mw_per_15_min"],
    }

# --------------------------------------------------------------------------------
# Fonction de calcul de la variale centrale_heure
# --------------------------------------------------------------------------------
def calculer_demande_heure(centrales_heure):
    return sum(centrale["production_demandee"] for centrale in centrales_heure)



data = charger_json(reference_consomation_data)
non_pilotable_data = charger_json(parc_non_pilotable_data)
params_temporels = charger_json(parametres_temporels_nucleaire_data)


prod_nucleaire_france = 0
min_prod_france = 0

for maximum in params_temporels["plants"]:
    prod_nucleaire_france += maximum["maximum_power_mw"]
    min_prod_france += maximum["minimum_operating_power_mw"]


demande_residuelle = (np.array(data["national_total_consumption_mw"]) - np.array(non_pilotable_data["national_total_production_mw"]["solar_plus_wind"])).tolist()

#print (demande_residuelle)

pourc_prod = (np.array(demande_residuelle) / prod_nucleaire_france).tolist()

prod_reelle = []
productions_sous_minimum = []
productions_sur_maximum = []

energie_a_revendre = []
energie_non_fournie = []

# ============================================================
# ETAT INITIAL DES CENTRALES
# ============================================================

etat_precedent = {}

for centrale in params_temporels["plants"]:
    etat_precedent[centrale["plant_id"]] = (centrale["initial_output_mw_at_23_45_previous_day"])


# ============================================================
# TRAITEMENT HEURE PAR HEURE
# ============================================================

for heure, pourcentage in zip(non_pilotable_data["timestamps"], pourc_prod):

    centrales_heure = []

    # ========================================================
    # CALCUL DE LA PRODUCTION DEMANDEE
    # ET DES LIMITES POUR CE QUART D'HEURE
    # ========================================================

    demande_heure = 0

    for centrale in params_temporels["plants"]:
        centrales_heure = calculer_centrales_heure(centrale, pourcentage, etat_precedent)
        demande_heure = calculer_demande_heure(centrales_heure)
        
        # plant_id = centrale["plant_id"]

        # production_demandee = (centrale["maximum_power_mw"] * pct)

        # minimum_technique = (centrale["minimum_operating_power_mw"])

        # maximum_technique = (centrale["maximum_power_mw"])

        # production_precedente = (etat_precedent[plant_id])

        # # Limite imposée par la vitesse de descente
        # minimum_temporel = (production_precedente - centrale["max_ramp_down_mw_per_15_min"])

        # # Limite imposée par la vitesse de montée
        # maximum_temporel = (production_precedente + centrale["max_ramp_up_mw_per_15_min"])

        # # Combinaison des limites techniques et temporelles
        # minimum_autorise = max(minimum_technique, minimum_temporel)

        # maximum_autorise = min(maximum_technique, maximum_temporel)

        # demande_heure += production_demandee

        # centrales_heure.append({
        #     "plant_id": plant_id,
        #     "production": production_demandee,
        #     "production_demandee": production_demandee,

        #     "production_precedente": production_precedente,

        #     # Limites applicables pendant ce quart d'heure
        #     "minimum": minimum_autorise,
        #     "maximum": maximum_autorise,

        #     # Limites permanentes de la centrale
        #     "minimum_technique": minimum_technique,
        #     "maximum_technique": maximum_technique,

        #     "rampe_montee": (centrale["max_ramp_up_mw_per_15_min"]),

        #     "rampe_descente": (centrale["max_ramp_down_mw_per_15_min"])
        # })


    # ========================================================
    # CALCUL DES LIMITES GLOBALES
    # ========================================================

    production_minimale_totale = sum(centrale["minimum"] for centrale in centrales_heure)

    production_maximale_totale = sum(centrale["maximum"] for centrale in centrales_heure)


    # ========================================================
    # CAS 1
    #
    # LA DEMANDE EST INFERIEURE AU MINIMUM
    # DE TOUTES LES CENTRALES
    #
    # -> TOUTES LES CENTRALES AU MINIMUM
    # -> LE SURPLUS EST A REVENDRE
    # ========================================================

    if demande_heure < production_minimale_totale:

        energie_a_revendre_mw = (production_minimale_totale - demande_heure)

        for centrale in centrales_heure:

            if centrale["production"] < centrale["minimum"]:

                productions_sous_minimum.append({
                    "plant_id": centrale["plant_id"],
                    "heure": heure,
                    "production_demandee": centrale["production_demandee"],
                    "production_minimum": centrale["minimum"],
                    "surplus": centrale["minimum"] - centrale["production"]
                })

            centrale["production"] = (centrale["minimum"])

        energie_a_revendre.append({
            "heure": heure,
            "demande_mw": demande_heure,
            "production_minimale_mw": production_minimale_totale,
            "energie_a_revendre_mw": energie_a_revendre_mw

        })

        # ----------------------------------------------------
        # ENREGISTREMENT
        # ----------------------------------------------------

        enregistrer_productions(centrales_heure, heure, prod_reelle, etat_precedent)

        continue


    # ========================================================
    # CAS 2
    #
    # LA DEMANDE EST SUPERIEURE AU MAXIMUM
    # DE TOUTES LES CENTRALES
    #
    # -> TOUTES LES CENTRALES AU MAXIMUM
    # -> ENERGIE NON FOURNIE
    # ========================================================

    if demande_heure > production_maximale_totale:

        energie_non_fournie_mw = (demande_heure - production_maximale_totale)

        for centrale in centrales_heure:

            if centrale["production"] > centrale["maximum"]:

                productions_sur_maximum.append({
                    "plant_id": centrale["plant_id"],
                    "heure": heure,
                    "production_demandee": centrale["production_demandee"],
                    "production_maximum": centrale["maximum"],
                    "deficit": (centrale["production"] - centrale["maximum"])
                })

            centrale["production"] = centrale["maximum"]

        energie_non_fournie.append({
            "heure": heure,
            "demande_mw": demande_heure,
            "production_maximale_mw": production_maximale_totale,
            "energie_non_fournie_mw": energie_non_fournie_mw

        })

        # ----------------------------------------------------
        # ENREGISTREMENT
        # ----------------------------------------------------
        enregistrer_productions(centrales_heure, heure, prod_reelle, etat_precedent)

        continue


    # ========================================================
    # CAS NORMAL
    #
    # LA DEMANDE EST COMPRISE ENTRE :
    #
    # minimum total <= demande <= maximum total
    #
    # ON COMMENCE PAR IDENTIFIER LES CENTRALES
    # HORS LIMITES
    # ========================================================

    surplus_a_retirer = 0
    deficit_a_repartir = 0


    # ========================================================
    # CENTRALES SOUS LE MINIMUM
    # ========================================================

    for centrale in centrales_heure:

        if centrale["production"] < centrale["minimum"]:

            surplus = (
                centrale["minimum"]
                - centrale["production"]
            )

            surplus_a_retirer += surplus

            productions_sous_minimum.append({
                "plant_id": centrale["plant_id"],
                "heure": heure,
                "production_demandee": centrale["production_demandee"],
                "production_minimum": centrale["minimum"],
                "surplus": surplus

            })

            centrale["production"] = centrale["minimum"]


    # ========================================================
    # CENTRALES AU-DESSUS DU MAXIMUM
    # ========================================================

    for centrale in centrales_heure:

        if centrale["production"] > centrale["maximum"]:

            deficit = centrale["production"] - centrale["maximum"]

            deficit_a_repartir += deficit

            productions_sur_maximum.append({
                "plant_id": centrale["plant_id"],
                "heure": heure,
                "production_demandee": centrale["production_demandee"],
                "production_maximum": centrale["maximum"],
                "deficit": deficit

            })

            centrale["production"] = centrale["maximum"]


    # ========================================================
    # REDISTRIBUTION DU SURPLUS
    #
    # Les centrales remontées au minimum créent
    # un surplus qu'il faut retirer aux autres.
    # ========================================================

    while surplus_a_retirer > 0.000001:

        centrales_disponibles = [

            centrale

            for centrale in centrales_heure

            if centrale["production"]
            > centrale["minimum"] + 0.000001

        ]


        # ----------------------------------------------------
        # AUCUNE CENTRALE NE PEUT PLUS BAISSER
        # ----------------------------------------------------

        if not centrales_disponibles:

            energie_a_revendre_mw = surplus_a_retirer

            energie_a_revendre.append({
                "heure": heure,
                "demande_mw": demande_heure,
                "production_mw": sum(centrale["production"] for centrale in centrales_heure),
                "energie_a_revendre_mw": energie_a_revendre_mw
            })

            break


        # ----------------------------------------------------
        # REDISTRIBUTION EQUITABLE
        # ----------------------------------------------------

        reduction_par_centrale = surplus_a_retirer / len(centrales_disponibles)
        
        surplus_restant = 0

        for centrale in centrales_disponibles:

            marge_reduction = centrale["production"] - centrale["minimum"]

            reduction = min(reduction_par_centrale, marge_reduction)

            centrale["production"] -= reduction

            surplus_restant += (reduction_par_centrale - reduction)


        surplus_a_retirer = surplus_restant


    # ========================================================
    # REDISTRIBUTION DU DEFICIT
    #
    # Les centrales plafonnées au maximum créent
    # un déficit qu'il faut fournir par les autres.
    # ========================================================

    while deficit_a_repartir > 0.000001:

        centrales_disponibles = [

            centrale

            for centrale in centrales_heure

            if centrale["production"]
            < centrale["maximum"] - 0.000001

        ]


        # ----------------------------------------------------
        # AUCUNE CENTRALE NE PEUT PLUS MONTER
        # ----------------------------------------------------

        if not centrales_disponibles:

            energie_non_fournie_mw = deficit_a_repartir

            energie_non_fournie.append({
                "heure": heure,
                "demande_mw": demande_heure,
                "production_mw": sum(centrale["production"] for centrale in centrales_heure),
                "energie_non_fournie_mw": energie_non_fournie_mw
            })

            break


        # ----------------------------------------------------
        # REDISTRIBUTION EQUITABLE
        # ----------------------------------------------------

        augmentation_par_centrale = deficit_a_repartir / len(centrales_disponibles)

        deficit_restant = 0

        for centrale in centrales_disponibles:

            marge_augmentation = centrale["maximum"] - centrale["production"]

            augmentation = min(augmentation_par_centrale, marge_augmentation)

            centrale["production"] += augmentation

            deficit_restant += (augmentation_par_centrale - augmentation)


        deficit_a_repartir = deficit_restant

    # ========================================================
    # ENREGISTREMENT DE LA PRODUCTION FINALE
    # ========================================================
    enregistrer_productions(centrales_heure, heure, prod_reelle, etat_precedent)

# ============================================================
# VERIFICATION DES RAMPES
# ============================================================

erreurs_rampes = []

for production in prod_reelle:

    variation = production["variation_mw"]

    if variation > production["rampe_montee_maximale"] + 0.000001:
        erreurs_rampes.append({
            "plant_id": production["plant_id"],
            "heure": production["heure"],
            "type": "montee_trop_rapide",
            "variation_mw": variation,
            "limite_mw": production["rampe_montee_maximale"]
        })

    if variation < -production["rampe_descente_maximale"] - 0.000001:
        erreurs_rampes.append({
            "plant_id": production["plant_id"],
            "heure": production["heure"],
            "type": "descente_trop_rapide",
            "variation_mw": variation,
            "limite_mw": production["rampe_descente_maximale"]
        })

print("NOMBRE D'ERREURS DE RAMPE :", len(erreurs_rampes))

print("ERREURS DE RAMPE :", erreurs_rampes)


# ============================================================
# AFFICHAGE
# ============================================================

print("NOMBRE DE PRODUCTIONS REELLES :", len(prod_reelle))

print("NOMBRE DE PRODUCTIONS SOUS MINIMUM :", len(productions_sous_minimum))

print("NOMBRE DE PRODUCTIONS SUR MAXIMUM :", len(productions_sur_maximum))

print("NOMBRE D'HEURES AVEC ENERGIE A REVENDRE :", len(energie_a_revendre))

print("NOMBRE D'HEURES AVEC ENERGIE NON FOURNIE :", len(energie_non_fournie))

print("\nPRODUCTIONS RÉELLES :")
print(prod_reelle[:40])

print("\nENERGIE A REVENDRE :")
print(energie_a_revendre)

print("\nENERGIE NON FOURNIE :")
print(energie_non_fournie)