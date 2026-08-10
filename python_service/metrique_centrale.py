from calcul_score_central import extract_data, calcul_scores

from dijkstra.region_service import RegionService
from dijkstra.json_repository import JsonRepository

repository = JsonRepository("data/parc-nucleaire-prescriptif-france.json")
region_service = RegionService(repository)
import main





def get_puissance_disponible(centrale):
    return (centrale["simulation"]["soft_upper_bound_mw"] - centrale["simulation"]["initial_output_mw"])

def get_centrale_disponible(centrale):
    return centrale["simulation"]["available"]

def get_taux_saturation(centrale):
    return centrale["simulation"]["soft_upper_bound_ratio"]

def get_nom_region(centrale):
    return centrale["location"]["region_name"]

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
         if (region_metriques["region"] == region):
            centrales_regionale.append(region_metriques)

    return centrales_regionale

def calcul_demande_residuelle(augmentation, region):
    centrales_regionale = get_centrale_regionale(region)

    puissance_disponible_regional = sum(centrale["puissance_disponible"] for centrale in centrales_regionale)
    demande_residuelle = augmentation - puissance_disponible_regional

    return demande_residuelle

def repartition(augmentation, region):
    demande_residuelle = calcul_demande_residuelle(augmentation, region)
    centrales_regionale = get_centrale_regionale(region)

    puissance_disponible_regional = sum(centrale["puissance_disponible"] for centrale in centrales_regionale)

    if (demande_residuelle <= 0):
        production_affectee = [centrale["puissance_disponible"] / puissance_disponible_regional * augmentation for centrale in centrales_regionale]
        repartition_locale = []

        for i, centrale in enumerate(centrales_regionale):
            repartition_locale.append({
                "central_id": centrale["central_id"],
                "production_affectee": production_affectee[i]
            })

        return repartition_locale
    else:
        repartition_locale = []
    
        for centrale in centrales_regionale:
            repartition_locale.append({
                "central_id": centrale["central_id"],
                "production_affectee": centrale["puissance_disponible"]
            })
        
        result = main.region_service.compute_routes(region)
        print(region)
        print(result)
        source_plant = result["source_plant"]
        candidats  = []
        for destination, route_info in result["routes"].items():

            if destination == source_plant:
                continue

            distance_km = route_info["distance_km"]
            total_loss_percent = route_info["total_loss_percent"]
            max_transfer_mw = route_info["max_transfer_mw"]

            print("DEBUG ROUTE :", destination)
            print("DEBUG ROUTE INFO :", route_info)
            print("DEBUG MAX TRANSFER :", max_transfer_mw)

            resultat = calcul_scores(
                source_plant,
                destination,
                distance_km,
                total_loss_percent,
                max_transfer_mw,
                demande_residuelle
            )

            candidats.append(resultat)

        candidats.sort(key=lambda x: x["score_candidat"])

        repartition_externe = []
        demande_restante = demande_residuelle
        index = 0

        while demande_restante > 0 and index < len(candidats):
            candidat = candidats[index]
            production_affectee = min(candidat["max_transfer_mw"], demande_restante)
            candidat["production_affectee"] = production_affectee 
            repartition_externe.append(candidat)
            demande_restante -= production_affectee
            index += 1

        return {
            "repartition_locale" : repartition_locale,
            "repartition_externe" : repartition_externe,
            "demande_non_couverte" : demande_restante
        }

