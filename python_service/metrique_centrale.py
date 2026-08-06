from calcul_score_central import extract_data, calcul_scores
from dijkstra.region_service import RegionService
from dijkstra.json_repository import JsonRepository

repository = JsonRepository("data/parc-nucleaire-prescriptif-france.json")
region_service = RegionService(repository)





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
        repository = JsonRepository("python_service/data/parc-nucleaire-prescriptif-france.json")
        region_service = RegionService(repository)

        result = region_service.compute_routes("occitanie")
        source_plant = result["source_plant"]
        resultats = []
        for destination, route_info in result["routes"].items():
            distance_km = route_info["distance_km"]
            total_loss_percent = route_info["total_loss_percent"]
            max_transfer_mw = route_info["max_transfer_mw"]

            resultat = calcul_scores(source_plant, destination, distance_km, total_loss_percent, max_transfer_mw, demande_residuelle)

            resultats.append(resultat)

        resultats.sort(key=lambda x: x["score_candidat"])
        

        resultats[0]["production_affectee"] = resultats[0]["max_transfer_mw"] - (resultats[0]["max_transfer_mw"] - demande_residuelle )
        repartition_region = resultats[0]


        return repartition_region

