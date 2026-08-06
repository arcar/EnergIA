from metrique_centrale import get_metrique_centrale, get_centrale_regionale, calcul_demande_residuelle, repartition
from calcul_score_central import extract_data, calcul_scores

def simuler_augmentation(region, augmentation):

    # 1. Récupérer les données centrales
    donnees = extract_data()

    # 2. Calculer les capacités
<<<<<<< HEAD
    metriques = get_metrique_centrale()
    centrales_regionale = []

    for region_metriques in metriques:
         if (region_metriques["region"] == region):
            centrales_regionale.append(region_metriques)

    puissance_disponible_regional = sum(centrale["puissance_disponible"] for centrale in centrales_regionale)
    demande_residuelle = augmentation - puissance_disponible_regional
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
=======
    #metriques c'est les calculs de toutes les régions et centrales_regionale c'es les calculs filtrer par régions
    metriques = get_metrique_centrale(donnees)
    centrales_regionale = get_centrale_regionale(region)
   
>>>>>>> 6edd2b9219e90f69e3b35e2c309be2c44226e078

    # 3. Sélectionner les meilleures centrales
    demande_residuelle = calcul_demande_residuelle(augmentation, region)

    # 4. Répartir la demande
    repartition = repartition(augmentation, region)

<<<<<<< HEAD



        return {
        "success": True,
        "region": region,
        "augmentation": augmentation,
        "centrales": centrales_regionale
=======
    return {
    "success": True,
    "region": region,
    "augmentation": augmentation,
    "centrales": repartition
>>>>>>> 6edd2b9219e90f69e3b35e2c309be2c44226e078
    }