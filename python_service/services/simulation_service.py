from metrique_centrale import get_metrique_centrale, get_centrale_regionale, calcul_demande_residuelle, repartition
from calcul_score_central import extract_data, calcul_scores
import logging

logger = logging.getLogger(__name__)

def simuler_augmentation(region, augmentation):

         # 1. Récupérer les données centrales
        logger.info(
            f"Début simulation - Région: {region}, Augmentation: {augmentation} MW"
        )

        donnees = extract_data()

        logger.info(
            f"Données chargées : {len(donnees['plants'])} centrales disponibles"
        )

        # 2. Calculer les capacités

        #metriques c'est les calculs de toutes les régions et centrales_regionale c'es les calculs filtrer par régions

        metriques = get_metrique_centrale()

        logger.info(
            f"Métriques calculées pour {len(metriques)} centrales"
        )

        centrales_regionale = get_centrale_regionale(region)

        logger.info(
         f"Centrales trouvées pour {region} : {len(centrales_regionale)}"
        )

        if len(centrales_regionale) == 0:
            logger.warning(
            f"Aucune centrale trouvée pour la région {region}"
        )

        

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