from metrique_centrale import metriques_centrales
from calcul_score_central import extract_data, calcul_scores

def simuler_augmentation(region, augmentation):

    # 1. Récupérer les données centrales
    donnees = extract_data()

    # 2. Calculer les capacités
    metriques = metriques_centrales(donnees)
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

    # 3. Sélectionner les meilleures centrales
    # (membre 2)

    # 4. Répartir la demande
    # (membre 3)

    return {
        "success": True,
        "region": region,
        "augmentation": augmentation,
        "centrales": centrales_regionale
    }