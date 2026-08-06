from calcul_score_central import extract_data
from dijkstra.region_service import RegionService
from dijkstra.json_repository import JsonRepository

repository = JsonRepository("python_service/data/parc-nucleaire-prescriptif-france.json")
region_service = RegionService(repository)

result = region_service.compute_routes("occitanie")

print(result)

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
    # else:
    #     #appeler la fonction dijsktra et calcul de score puis faire le calcul de repartition
    #     return repartition_regional