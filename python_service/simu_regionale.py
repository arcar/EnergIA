from simu_nationale import (charger_donnees, construire_centrales_heure, enregistrer_productions, EPSILON, initialiser_etat, verifier_rampes)
from metrique_centrale import (router_deficit)

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

def production_non_pilotable_detail_regional():
    detail = {}
    for non_pilotable in data["non_pilotable"]["regions"]:
        solar = non_pilotable["production_mw"]["solar"]
        wind = non_pilotable["production_mw"]["wind"]
        detail[non_pilotable["id"]] = {
            "solar_mw": solar,
            "wind_mw": wind,
            "total_mw": [s + w for s, w in zip(solar, wind)]
        }
    return detail


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
    return pourcentage_regional, facteur_reserve

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
            "maximum_regional_mw" : maximum_regional,
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
            "maximum_regional_mw" : maximum_regional,
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
        "maximum_regional_mw" : maximum_regional,
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

def plant_id_vers_region(regions_avec_nucleaire):
    mapping = {}
    for region in regions_avec_nucleaire:
        for centrale in region["plants"]:
            mapping[centrale["plant_id"]] = region["region_id"]
    return mapping

def repartir_surplus_vers_deficits(resultats_heure):
    surplus_regions = [r for r in resultats_heure if r["surplus_residuel"] > EPSILON]
    deficit_regions = [r for r in resultats_heure if r["deficit_residuel"] > EPSILON]

    echanges = []
    index_surplus = 0

    for deficit_region in deficit_regions:
        while deficit_region["deficit_residuel"] > EPSILON and index_surplus < len(surplus_regions):
            surplus_region = surplus_regions[index_surplus]

            if surplus_region["surplus_residuel"] <= EPSILON:
                index_surplus += 1
                continue

            transfert = min(
                deficit_region["deficit_residuel"],
                surplus_region["surplus_residuel"]
            )

            echanges.append({
                "region_source": surplus_region["region_id"],
                "region_destination": deficit_region["region_id"],
                "quantite_mw": transfert
            })

            deficit_region["deficit_residuel"] -= transfert
            surplus_region["surplus_residuel"] -= transfert

    return echanges

def resultats_regions_sans_nucleaire(regions_sans_nucleaire, demande_residuelle_toutes, index, ids_deconnectees):
    resultats = []

    for region in regions_sans_nucleaire:
        region_id = region["region_id"]

        if region_id in ids_deconnectees:
            continue

        valeur_demande = demande_residuelle_toutes[region_id][index]
        deficit = max(valeur_demande, 0)

        resultats.append({
            "region_id": region_id,
            "demande_mw": valeur_demande,
            "production_mw": 0,
            "maximum_regional_mw": 0,
            "surplus_residuel": 0,
            "deficit_residuel": deficit
        })

    return resultats

def capacite_max_par_region(regions_avec_nucleaire):
    capacites = {}
    for region in regions_avec_nucleaire:
        capacites[region["region_id"]] = sum(
            centrale["maximum_power_mw"] for centrale in region["plants"]
        )
    return capacites

def detecter_situation_degradee(region_id, heure, production_mw, maximum_regional_mw, capacite_max_region, minimum_reserve_percent):
    reserve_disponible_mw = maximum_regional_mw - production_mw

    if capacite_max_region > 0:
        reserve_disponible_percent = (reserve_disponible_mw / capacite_max_region) * 100
    else:
        reserve_disponible_percent = 0

    situation_degradee = reserve_disponible_percent < minimum_reserve_percent

    return {
        "region_id": region_id,
        "heure": heure,
        "production_mw": production_mw,
        "maximum_technique_mw": maximum_regional_mw,
        "capacite_max_region_mw": capacite_max_region,
        "reserve_disponible_mw": reserve_disponible_mw,
        "reserve_disponible_percent": reserve_disponible_percent,
        "seuil_minimum_percent": minimum_reserve_percent,
        "situation_degradee": situation_degradee,
    }

def construire_detail_regional(region_id, heure, index, production_mw, production_precedente_mw, consommation_par_region, non_pilotable_detail, demande_residuelle_toutes):
    variation_mw = production_mw - production_precedente_mw

    if variation_mw > EPSILON:
        sens_variation = "hausse"
    elif variation_mw < -EPSILON:
        sens_variation = "baisse"
    else:
        sens_variation = "stable"

    if region_id in non_pilotable_detail:
        solar_mw = non_pilotable_detail[region_id]["solar_mw"][index]
        wind_mw = non_pilotable_detail[region_id]["wind_mw"][index]
        non_pilotable_total_mw = non_pilotable_detail[region_id]["total_mw"][index]
    else:
        solar_mw = 0
        wind_mw = 0
        non_pilotable_total_mw = 0

    return {
        "region_id": region_id,
        "heure": heure,
        "consommation_mw": consommation_par_region[region_id][index],
        "solar_mw": solar_mw,
        "wind_mw": wind_mw,
        "non_pilotable_total_mw": non_pilotable_total_mw,
        "demande_residuelle_mw": demande_residuelle_toutes[region_id][index],
        "production_nucleaire_mw": production_mw,
        "production_nucleaire_precedente_mw": production_precedente_mw,
        "variation_mw": variation_mw,
        "sens_variation": sens_variation,
    }

def production_regionale_initiale(regions):
    initiale = {}
    for region in regions:
        initiale[region["region_id"]] = sum(
            centrale["initial_output_mw_at_23_45_previous_day"] for centrale in region["plants"]
        )
    return initiale

def equilibrage_local_toutes_regions_nucleaires():
    regions = regions_avec_centrales()
    pourcentages, facteur_reserve = pourcentage_repartition_regionale()
    demande_residuelle_toutes = demande_moins_non_pilotable()
    consommation_par_region = demande_regionale()
    non_pilotable_detail = production_non_pilotable_detail_regional()
    minimum_reserve_percent = 8.0

    etat_precedent = initialiser_etat(data["params_temporels"])

    prod_reelle = []
    productions_sous_minimum = []
    productions_sur_maximum = []
    resultats_toutes_regions = []
    resultats_routage = []
    echanges_surplus_deficit = []
    energie_non_fournie = []
    energie_a_revendre = []
    situations_degradees = []
    details_regionaux = []

    regions_avec_nucleaire = [region for region in regions if region["region_id"] in pourcentages]
    regions_sans_nucleaire = [region for region in regions if region["region_id"] not in pourcentages]
    regions_deconnectees = [region for region in data["parc_nucleaire"]["regions"] if not region["connected_to_continental_grid"]]
    ids_deconnectees = {region["id"] for region in regions_deconnectees}

    mapping = plant_id_vers_region(regions_avec_nucleaire)
    capacite_max_region_dict = capacite_max_par_region(regions_avec_nucleaire)

    production_regionale_precedente = production_regionale_initiale(regions)

    for index, quarts_heure in enumerate(data["consommation"]["timestamps"]):
        production_debut_heure = dict(etat_precedent)

        resultats_heure = []

        for region in regions_avec_nucleaire:
            resultat = equilibrer_region_localement(region["region_id"], quarts_heure, region["plants"], pourcentages[region["region_id"]][index], etat_precedent, prod_reelle, productions_sous_minimum, productions_sur_maximum)
            resultats_heure.append(resultat)

            situation = detecter_situation_degradee(
                resultat["region_id"], quarts_heure, resultat["production_mw"],
                resultat["maximum_regional_mw"], capacite_max_region_dict[resultat["region_id"]],
                minimum_reserve_percent
            )
            situations_degradees.append(situation)

        resultats_heure.extend(
            resultats_regions_sans_nucleaire(regions_sans_nucleaire, demande_residuelle_toutes, index, ids_deconnectees)
        )

        echanges = repartir_surplus_vers_deficits(resultats_heure)
        echanges_surplus_deficit.extend(echanges)

        for resultat in resultats_heure:
            region_id = resultat["region_id"]

            if resultat["deficit_residuel"] > EPSILON:
                gerer_deficit = router_deficit(region_id, resultat["deficit_residuel"], etat_precedent, facteur_reserve, data["params_temporels"]["plants"], mapping, production_debut_heure)
                resultats_routage.append(gerer_deficit)

                if gerer_deficit["demande_non_couverte"] > EPSILON:
                    energie_non_fournie.append({
                        "region_id": region_id,
                        "heure": quarts_heure,
                        "energie_non_fournie_mw": gerer_deficit["demande_non_couverte"]
                    })

            if resultat["surplus_residuel"] > EPSILON:
                energie_a_revendre.append({
                    "region_id": region_id,
                    "heure": quarts_heure,
                    "energie_a_revendre_mw": resultat["surplus_residuel"]
                })

            detail = construire_detail_regional(region_id, quarts_heure, index, resultat["production_mw"], production_regionale_precedente[region_id], consommation_par_region, non_pilotable_detail, demande_residuelle_toutes)
            details_regionaux.append(detail)

            production_regionale_precedente[region_id] = resultat["production_mw"]

        resultats_toutes_regions.extend(resultats_heure)

    erreurs_rampes = verifier_rampes(prod_reelle)

    return {
        "resultats_toutes_regions": resultats_toutes_regions,
        "prod_reelle": prod_reelle,
        "productions_sous_minimum": productions_sous_minimum,
        "productions_sur_maximum": productions_sur_maximum,
        "resultats_routage": resultats_routage,
        "echanges_surplus_deficit": echanges_surplus_deficit,
        "energie_non_fournie": energie_non_fournie,
        "energie_a_revendre": energie_a_revendre,
        "situations_degradees": situations_degradees,
        "details_regionaux": details_regionaux,
        "erreurs_rampes": erreurs_rampes,
    }

def repartition_par_heure(prod_reelle, heure_demandee):
    resultats = []

    for entree in prod_reelle:
        if entree["heure"] != heure_demandee:
            continue

        centrale = trouver_centrales(entree["plant_id"])
        puissance_max = centrale["maximum_power_mw"]

        taux_utilisation = (entree["production"] / puissance_max) * 100 if puissance_max > 0 else 0

        resultats.append({
            "plant_id": entree["plant_id"],
            "plant_name": centrale["plant_name"],
            "heure": entree["heure"],
            "production_mw": entree["production"],
            "production_demandee_mw": entree["production_demandee"],
            "puissance_maximum_mw": puissance_max,
            "puissance_minimum_mw": centrale["minimum_operating_power_mw"],
            "taux_utilisation_percent": taux_utilisation,
            "minimum_autorise_mw": entree["minimum_autorise"],
            "maximum_autorise_mw": entree["maximum_autorise"],
            "variation_mw": entree["variation_mw"],
        })

    return resultats

resultats = equilibrage_local_toutes_regions_nucleaires()
repartition_heure_test = repartition_par_heure(resultats["prod_reelle"], "10:00")
print(repartition_heure_test)
