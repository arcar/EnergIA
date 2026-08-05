<<<<<<< HEAD
from calcul_score_central import extract_data
from metrique_centrale import get_metrique_centrale
=======
from calcul_score_central import extract_data, metriques_centrales
>>>>>>> 9e7a176ec57a080dc0858a69ba4e82a52b90866a

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