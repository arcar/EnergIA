from metrique_centrale import get_metrique_centrale, get_centrale_regionale, calcul_demande_residuelle, repartition
from calcul_score_central import extract_data
import logging
logger = logging.getLogger(__name__)

def simuler_augmentation(region, augmentation):

    logger.info(
        f"Nouvelle simulation demandée - Région: {region}, "
        f"Augmentation: {augmentation} MW"
    )

    # 1. Récupérer les métriques de toutes les centrales
    metriques = get_metrique_centrale()

    logger.info(
        f"Nombre total de centrales analysées : {len(metriques)}"
    )

    # 2. Filtrer les centrales de la région demandée
    logger.info(f"Vérification de la région : {region}")

    centrales_regionale = get_centrale_regionale(region)

    logger.info(
        f"Nombre de centrales trouvées dans {region} : "
        f"{len(centrales_regionale)}"
    )

    logger.debug(
        f"Centrales régionales : {centrales_regionale}"
    )

    # 3. Calculer la demande résiduelle
    demande_residuelle, puissance_disponible_regional = calcul_demande_residuelle(
        augmentation,
        region
    )

    logger.info(
        f"Demande résiduelle pour {region} : "
        f"{demande_residuelle} MW"
    )

    # 4. Répartir la demande
    logger.info("Début de la répartition de la demande")

    resultat_repartition = repartition(
        augmentation,
        region
    )

    print("===== DEBUG APRES REPARTITION =====")
    print(resultat_repartition)
    print("===================================")

    logger.info("Répartition terminée")

    print("===== DEBUG AVANT RETURN =====")
    print("Simulation terminée")
    print("==============================")
    
    return {
        "success": True,
        "region": region,
        "augmentation": augmentation,
        "centrales": resultat_repartition
    }

