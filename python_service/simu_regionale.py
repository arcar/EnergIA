from simu_nationale import (charger_donnees, construire_centrales_heure, enregistrer_productions, EPSILON, initialiser_etat)

data = charger_donnees()

def trouver_centrales(plant_id):
    for centrale in data["params_temporels"]["plants"]:
        if centrale["plant_id"] == plant_id:
            return centrale
    raise ValueError(f"Centrale {plant_id} introuvable dans params_temporels")

def regions_avec_centrales():
    regions = []

    for region in data["parc_nucleaire"]["regions"]:
        centrales_region = [trouver_centrales(plant_id) for plant_id in region["local_plant_ids"] if not plant_id.startswith("PDL_")]

        regions.append({
            "region_id" :  region["id"],
            "plants": centrales_region
        })

    return regions

def demande_regionale():
    consommation_region = {}
    for region in data["consommation"]["regions"]:
        consommation_region[region["id"]] = region["consumption_mw"]

    return consommation_region

def production_non_pilotables_regional():
    production_np_regional = {}
    for non_pilotable in data["non_pilotable"]["regions"]:
        solar = non_pilotable["production_mw"]["solar"]
        wind = non_pilotable["production_mw"]["wind"]
        production_np_regional[non_pilotable["id"]] = [
            production_solaire + production_eolienne for production_solaire, production_eolienne in zip(solar, wind)
        ]
    return production_np_regional


def demande_moins_non_pilotable():
    consommation = demande_regionale()
    production_np = production_non_pilotables_regional()

    demande_residuelle = {}

    for region in consommation:
        demande_residuelle[region] = [
            valeur_consommation - valeur_production for valeur_consommation, valeur_production in zip(consommation[region], production_np[region])
        ]

    return demande_residuelle

def pourcentage_repartition_regionale():
    regions = regions_avec_centrales()
    demande_residuelle = demande_moins_non_pilotable()
    minimum_reserve_percent = 8.0
    facteur_reserve = 1 - (minimum_reserve_percent / 100)
    pourcentage_regional = {}

    for region in regions:
        if region["plants"] == None:
            continue

        capacite_max_region = sum(centrales["maximum_power_mw"] for centrales in region["plants"] if centrales is not None)

        if capacite_max_region == 0:
            continue
        capacite_dispo_region = capacite_max_region * facteur_reserve

        demande_residuelle_region = demande_residuelle[region["region_id"]]

        pourcentage_regional[region["region_id"]] = [
            valeur_demande / capacite_dispo_region for valeur_demande in demande_residuelle_region
        ]
    return pourcentage_regional

def sous_minimum(centrales_heure, heure, productions_sous_minimum):

    surplus_a_retirer = 0

    for centrale in centrales_heure:
        if centrale["production"] < centrale["minimum"]:
            surplus = centrale["minimum"] - centrale["production"]

            surplus_a_retirer += surplus

            productions_sous_minimum.append({
                "plant_id": centrale["plant_id"],
                "heure": heure,
                "production_demandee": (centrale["production_demandee"]),
                "production_minimum": (centrale["minimum"]),
                "surplus": surplus
            })

            centrale["production"] = centrale["minimum"]

    return surplus_a_retirer

def sur_maximum(centrales_heure, heure, productions_sur_maximum):
    deficit_a_repartir = 0

    for centrale in centrales_heure:
        if centrale["production"] > centrale["maximum"]:
            deficit = centrale["production"] - centrale["maximum"]

            deficit_a_repartir += deficit

            productions_sur_maximum.append({
                "plant_id": centrale["plant_id"],
                "heure": heure,
                "production_demandee": (centrale["production_demandee"]),
                "production_minimum": (centrale["minimum"]),
                "deficit": deficit
            })

            centrale["production"] = centrale["maximum"]

    return deficit_a_repartir




def limites_globales(centrales_heure):

    production_minimal = sum(centrale["minimum"] for centrale in centrales_heure)

    production_maximal = sum(centrale["maximum"] for centrale in centrales_heure)

    return production_minimal, production_maximal

def calculer_demande_heure(centrales_heure):
    return sum(centrale["production_demandee"] for centrale in centrales_heure)

def equilibrer_region_localement(region_id, heure, centrales, pourcentage, etat_precedent, prod_reelle, productions_sous_minimum, productions_sur_maximum):
    centrales_heure = construire_centrales_heure(centrales, pourcentage, etat_precedent)
    demande_heure = calculer_demande_heure(centrales_heure)
    minimum_regional, maximum_regional = limites_globales(centrales_heure)
    if demande_heure < minimum_regional:
        surplus_residuel = minimum_regional - demande_heure
        for centrale in centrales_heure:   
            centrale["production"] = centrale["minimum"]

        enregistrer_productions(centrales_heure, heure, prod_reelle, etat_precedent)
        return {
            "region_id" : region_id,
            "demande_mw" : demande_heure,
            "production_mw" : minimum_regional,
            "surplus_residuel" : surplus_residuel,
            "deficit_residuel" : 0
        }
    if demande_heure >  maximum_regional:
        deficit_residuel = demande_heure - maximum_regional

        for centrale in centrales_heure:
            centrale["production"] = centrale["maximum"]

        enregistrer_productions(centrales_heure, heure, prod_reelle, etat_precedent)

        return {
            "region_id" : region_id,
            "demande_mw" : demande_heure,
            "production_mw" : maximum_regional,
            "surplus_residuel" : 0,
            "deficit_residuel" : deficit_residuel
        }

    surplus_a_retirer = sous_minimum(centrales_heure, heure, productions_sous_minimum)
    deficit_a_repartir = sur_maximum(centrales_heure, heure, productions_sur_maximum)

    surplus_restant = redistribuer_surplus(centrales_heure, surplus_a_retirer)
    deficit_restant = redistribuer_deficit(centrales_heure, deficit_a_repartir)

    enregistrer_productions(centrales_heure, heure, prod_reelle, etat_precedent)

    return {
        "region_id" : region_id,
        "demande_mw" : demande_heure,
        "production_mw" :  sum(centrale["production"] for centrale in centrales_heure),
        "surplus_residuel" : surplus_restant,
        "deficit_residuel" : deficit_restant
    }

def redistribuer(centrales_heure, quantite, borne, operation):
    while quantite > EPSILON:

        centrales_disponibles = [
            centrale for centrale in centrales_heure if borne(centrale)
        ]

        if not centrales_disponibles:
            break

        variation_par_centrale = quantite / len(centrales_disponibles)

        quantite_restante = 0

        for centrale in centrales_disponibles:
            variation, reste = operation(centrale, variation_par_centrale)
            centrale["production"] += variation
            quantite_restante += reste

        quantite = quantite_restante
    return quantite


def redistribuer_surplus(centrales_heure, surplus_a_retirer): 

    return redistribuer(
        centrales_heure, surplus_a_retirer,
        lambda centrale : centrale["production"] > centrale["minimum"] + EPSILON,
        lambda centrale, reduction_demandee: (
            (-min(reduction_demandee, centrale["production"] - centrale["minimum"])),
            (reduction_demandee - min(reduction_demandee, centrale["production"] - centrale["minimum"]))
        )
    )

def redistribuer_deficit(centrales_heure, deficit_a_repartir):

    return redistribuer(
        centrales_heure, deficit_a_repartir,
        lambda centrale : centrale["production"] < centrale["maximum"] - EPSILON,
        lambda centrale, augmentation_demandee: (
            (min(augmentation_demandee, centrale["maximum"] - centrale["production"])),
            (augmentation_demandee - min(augmentation_demandee, centrale["maximum"] - centrale["production"]))
        )
    )

def equilibrage_local_toutes_regions_nucleaires():
    regions = regions_avec_centrales()
    pourcentages = pourcentage_repartition_regionale()

    etat_precedent = initialiser_etat(data["params_temporels"])

    prod_reelle = []
    productions_sous_minimum = []
    productions_sur_maximum = []
    resultats_toutes_regions = []

    regions_avec_nucleaire =  [region for region in regions if region["region_id"] in pourcentages]
    regions_sans_nucleaire = [region for region in regions if region["region_id"] not in pourcentages]
    regions_deconnectees = [region for region in data["parc_nucleaire"]["regions"] if not region["connected_to_continental_grid"]]

    for index, quarts_heure in enumerate(data["consommation"]["timestamps"]):
        for region in regions_avec_nucleaire:
            resultat = equilibrer_region_localement(region["region_id"], quarts_heure,region["plants"], pourcentages[region["region_id"]][index], etat_precedent, prod_reelle, productions_sous_minimum, productions_sur_maximum)
            resultats_toutes_regions.append(resultat) 

    return resultats_toutes_regions, prod_reelle, productions_sous_minimum, productions_sur_maximum

