from calcul_score_central import extract_data, calcul_scores, find_centrale, extract_production, extract_consomation_temporels

from dijkstra.region_service import RegionService
from dijkstra.json_repository import JsonRepository
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
json_file = BASE_DIR / "data" / "parc-nucleaire-prescriptif-france.json"

repository = JsonRepository(str(json_file))

#repository = JsonRepository("data/parc-nucleaire-prescriptif-france.json")
region_service = RegionService(repository)






def get_puissance_disponible(centrale):
    return (centrale["simulation"]["soft_upper_bound_mw"] - centrale["simulation"]["initial_output_mw"])

def get_centrale_disponible(centrale):
    return centrale["simulation"]["available"]

def get_taux_saturation(centrale):
    return centrale["simulation"]["soft_upper_bound_ratio"]

def get_nom_region(centrale):
    return centrale["location"]["region_id"]

def get_central_id(centrale):
    return centrale["id"]

def get_metrique_centrale():
    donnees = extract_data()
    metriques = []

    for centrale in donnees["plants"]:

        metriques.append({
            "puissance_disponible" : get_puissance_disponible(centrale),
            "taux_saturation": get_taux_saturation(centrale),
            "disponible": get_centrale_disponible(centrale),
            "region": get_nom_region(centrale),
            "central_id": get_central_id(centrale)
        })

    metriques.sort(key=lambda x: x["region"])
    return metriques

def get_centrale_regionale(region):
    metriques = get_metrique_centrale()
    centrales_regionale = []
    
    for region_metriques in metriques:
         if (region_metriques["region"].lower() == region.lower()):
            centrales_regionale.append(region_metriques)

    return centrales_regionale

def calcul_demande_residuelle(augmentation, region):
    centrales_regionale = get_centrale_regionale(region)

    puissance_disponible_regional = sum(centrale["puissance_disponible"] for centrale in centrales_regionale)
    demande_residuelle = augmentation - puissance_disponible_regional

    return demande_residuelle, puissance_disponible_regional

def match_central_region():
    donnees_centrale = extract_production()
    donnees_parc_nucleaire = extract_data()
    resultats = []

    for centrales in donnees_centrale["plants"]:
        for centrale_parc_nucleaire in donnees_parc_nucleaire["plants"]:
            if (centrales["plant_id"] == centrale_parc_nucleaire["id"]):
                resultats.append({
                    "region": centrale_parc_nucleaire["location"]["region_id"],
                    "centrale": centrales["plant_id"],
                    "initial_output_mw" : centrales["initial_output_mw_at_23_45_previous_day"],
                    "minimum_operating_power_mw" : centrales["minimum_operating_power_mw"],
                    "maximum_power_mw" : centrales["maximum_power_mw"],
                    "max_ramp_up_mw_per_15_min" : centrales["max_ramp_up_mw_per_15_min"],
                    "max_ramp_down_mw_per_15_min" : centrales["max_ramp_down_mw_per_15_min"]
                })
    return resultats

def calcul_prodduction_regional():
    donnees_centrale_regional = match_central_region()

    production_regional_initial = []

    for centrale in donnees_centrale_regional:
        region = centrale["region"]
        production = centrale["initial_output_mw"]

        region_existe = False

        for resultat in production_regional_initial:
            if resultat["region"] == region:
                resultat["production_initial"] += production
                region_existe = True
                break

        if not region_existe:
            production_regional_initial.append({
                "region": region,
                "production_initial": production
            })

    return production_regional_initial

def repartition_locale():
    production_regional_initial = calcul_prodduction_regional()
    donnees_regions = extract_consomation_temporels()
    donnees_centrales_regional= match_central_region()

    for region, production in production_regional_initial:
        
def repartition():
    production_regional_initial = calcul_prodduction_regional()
    donnees_regions = extract_consomation_temporels()
    donnees_centrales_regional= match_central_region()

    regions_ordered = sorted(donnees_regions["regions"], key=lambda region: region["spring_reference_average_mw"], reverse=True)

    for region in regions_ordered:


    for regions in donnees["regions"]:
        if(region == regions["id"]):
            if (regions["connected_to_continental_grid"] == False):
                return {"reponse": "La région n'est pas connecté au réseau national"}
    
    if (demande_residuelle <= 0):
        production_affectee = [centrale["puissance_disponible"] / puissance_disponible_regional * augmentation for centrale in centrales_regionale]
        repartition_locale = []

        for i, centrale in enumerate(centrales_regionale):
            repartition_locale.append({
                "central_id": centrale["central_id"],
                "production_affectee": production_affectee[i],
                "production_restante": (
                    centrale["puissance_disponible"] - production_affectee[i]
                )
            })

        return repartition_locale
    else:
        repartition_locale = []
    
        for centrale in centrales_regionale:
            repartition_locale.append({
                "central_id": centrale["central_id"],
                "production_affectee": centrale["puissance_disponible"],
                "production_restante": 0
                
            })
        
        result = region_service.compute_routes(region)
        print(region)
        print(result)
        source_plant = result["source_plant"]

        donnees = extract_data()
        plant_ids = set(p["id"] for p in donnees["plants"])

        candidats  = []
        for destination, route_info in result["routes"].items():

            centrale = find_centrale(extract_data()["plants"], destination)

            if centrale is not None and centrale["location"]["region_name"] == region:
                print("DESTINATION DANS LA REGION :", destination)
                continue

            if destination == source_plant:
                continue

            distance_km = route_info["distance_km"]
            total_loss_percent = route_info["total_loss_percent"]
            max_transfer_mw = route_info["max_transfer_mw"]

            

            

            resultat = calcul_scores(
                source_plant,
                destination,
                distance_km,
                total_loss_percent,
                max_transfer_mw,
                demande_residuelle
            )
            if resultat is not None:
                candidats.append(resultat)

        candidats.sort(key=lambda x: x["score_candidat"])

        repartition_externe = []
        demande_restante = demande_residuelle
        index = 0

        while demande_restante > 0 and index < len(candidats):
            candidat = candidats[index]
            production_affectee = min(
                candidat["puissance_disponible"],
                candidat["max_transfer_mw"],
                demande_restante
            )
            candidat["production_affectee"] = production_affectee 
            repartition_externe.append(candidat)
            demande_restante -= production_affectee
            index += 1
            candidat["production_restante"] = (
                candidat["puissance_disponible"] - production_affectee
            )

        return {
            "repartition_locale" : repartition_locale,
            "repartition_externe" : repartition_externe,
            "demande_non_couverte" : demande_restante
        }

def consommation_regionale():
    donnees_regionale = extract_consomation_temporels
    for region in donnees_regionale["regions"]:
        for consomation_quart in region["consumption_mw"]:
            return {
                "region_id" : region["id"],
                "consomation_quart": consomation_quart
            }

def repartitionX(augmentation, region):
    donnees = extract_data()
    demande_residuelle, puissance_disponible_regional = calcul_demande_residuelle(augmentation, region)
    centrales_regionale = get_centrale_regionale(region)

    for regions in donnees["regions"]:
        if(region == regions["id"]):
            if (regions["connected_to_continental_grid"] == False):
                return {"reponse": "La région n'est pas connecté au réseau national"}
    
    if (demande_residuelle <= 0):
        production_affectee = [centrale["puissance_disponible"] / puissance_disponible_regional * augmentation for centrale in centrales_regionale]
        repartition_locale = []

        for i, centrale in enumerate(centrales_regionale):
            repartition_locale.append({
                "central_id": centrale["central_id"],
                "production_affectee": production_affectee[i],
                "production_restante": (
                    centrale["puissance_disponible"] - production_affectee[i]
                )
            })

        return repartition_locale
    else:
        repartition_locale = []
    
        for centrale in centrales_regionale:
            repartition_locale.append({
                "central_id": centrale["central_id"],
                "production_affectee": centrale["puissance_disponible"],
                "production_restante": 0
                
            })
        
        result = region_service.compute_routes(region)
        print(region)
        print(result)
        source_plant = result["source_plant"]

        donnees = extract_data()
        plant_ids = set(p["id"] for p in donnees["plants"])

        candidats  = []
        for destination, route_info in result["routes"].items():

            centrale = find_centrale(extract_data()["plants"], destination)

            if centrale is not None and centrale["location"]["region_name"] == region:
                print("DESTINATION DANS LA REGION :", destination)
                continue

            if destination == source_plant:
                continue

            distance_km = route_info["distance_km"]
            total_loss_percent = route_info["total_loss_percent"]
            max_transfer_mw = route_info["max_transfer_mw"]

            

            

            resultat = calcul_scores(
                source_plant,
                destination,
                distance_km,
                total_loss_percent,
                max_transfer_mw,
                demande_residuelle
            )
            if resultat is not None:
                candidats.append(resultat)

        candidats.sort(key=lambda x: x["score_candidat"])

        repartition_externe = []
        demande_restante = demande_residuelle
        index = 0

        while demande_restante > 0 and index < len(candidats):
            candidat = candidats[index]
            production_affectee = min(
                candidat["puissance_disponible"],
                candidat["max_transfer_mw"],
                demande_restante
            )
            candidat["production_affectee"] = production_affectee 
            repartition_externe.append(candidat)
            demande_restante -= production_affectee
            index += 1
            candidat["production_restante"] = (
                candidat["puissance_disponible"] - production_affectee
            )

        return {
            "repartition_locale" : repartition_locale,
            "repartition_externe" : repartition_externe,
            "demande_non_couverte" : demande_restante
        }