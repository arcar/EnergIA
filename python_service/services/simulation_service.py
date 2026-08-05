
from calcul_score_central import extract_data
from metrique_centrale import get_metrique_centrale


def simuler_augmentation(region, augmentation):

    # 1. Récupérer les données centrales
    donnees = extract_data()

    # 2. Calculer les capacités
    centrales = get_metrique_centrale()

    # 3. Sélectionner les meilleures centrales
    # (membre 2)

    # 4. Répartir la demande
    # (membre 3)

    return {
        "success": True,
        "region": region,
        "augmentation": augmentation,
        "centrales": centrales
    }