from metrique_centrale import get_metrique_centrale, get_centrale_regionale, calcul_demande_residuelle, repartition
from calcul_score_central import extract_data

def simuler_augmentation(region, augmentation):
    # 1. Récupérer les données centrales
    # donnees = extract_data()

    # 2. Calculer les capacités
    #metriques c'est les calculs de toutes les régions et centrales_regionale c'es les calculs filtrer par régions
    metriques = get_metrique_centrale()
    centrales_regionale = get_centrale_regionale(region)
   

    # 3. Sélectionner les meilleures centrales
    demande_residuelle = calcul_demande_residuelle(augmentation, region)

    logger.info(
        f"Demande résiduelle : {demande_residuelle} MW"
    )


    # 4. Répartir la demande
    resultat_repartition = repartition(augmentation, region)

    logger.info(
        "Répartition terminée avec succès"
    )

    return {
        "success": True,
        "region": region,
        "augmentation": augmentation,
        "centrales": resultat_repartition
    }

