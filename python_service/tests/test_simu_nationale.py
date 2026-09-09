from simu_nationale import calculer_centrale_heure
from unittest.mock import patch

def test_limite_max_centrale():
    centrale = {
        "plant_id": "flamanville",
        "maximum_power_mw": 1000,
        "minimum_operating_power_mw": 200,
        "max_ramp_up_mw_per_15_min": 300,
        "max_ramp_down_mw_per_15_min": 150
    }

    etat_precedent = {
        "flamanville": 900
    }

    pourcentage = 1.2

    resultat = calculer_centrale_heure(centrale, pourcentage, etat_precedent)

    # Production demandée :
    assert resultat["production"] == 1200
    assert resultat["production_demandee"] == 1200

    # Production de l'heure précédente
    assert resultat["production_precedente"] == 900

    # Limites techniques
    assert resultat["minimum_technique"] == 200
    assert resultat["maximum_technique"] == 1000

    assert resultat["minimum"] == 750
    assert resultat["maximum"] == 1000

    # Valeurs des rampes
    assert resultat["rampe_montee"] == 300
    assert resultat["rampe_descente"] == 150

    # Identifiant de la centrale
    assert resultat["plant_id"] == "flamanville"


def test_ramp_up_centrale():
    centrale = {
        "plant_id": "flamanville",
        "maximum_power_mw": 1000,
        "minimum_operating_power_mw": 200,
        "max_ramp_up_mw_per_15_min": 100,
        "max_ramp_down_mw_per_15_min": 150
    }

    etat_precedent = {
        "flamanville": 600
    }

    pourcentage = 0.8

    resultat = calculer_centrale_heure(centrale, pourcentage, etat_precedent)

    # Production demandée :
    assert resultat["production"] == 800
    assert resultat["production_demandee"] == 800

    # Production de l'heure précédente
    assert resultat["production_precedente"] == 600

    # Limites techniques
    assert resultat["minimum_technique"] == 200
    assert resultat["maximum_technique"] == 1000

    assert resultat["minimum"] == 450
    assert resultat["maximum"] == 700

    # Valeurs des rampes
    assert resultat["rampe_montee"] == 100
    assert resultat["rampe_descente"] == 150

    # Identifiant de la centrale
    assert resultat["plant_id"] == "flamanville"


def test_ramp_down_centrale():
    centrale = {
        "plant_id": "flamanville",
        "maximum_power_mw": 1000,
        "minimum_operating_power_mw": 200,
        "max_ramp_up_mw_per_15_min": 100,
        "max_ramp_down_mw_per_15_min": 150
    }

    etat_precedent = {
        "flamanville": 800
    }

    pourcentage = 0.6

    resultat = calculer_centrale_heure(centrale, pourcentage, etat_precedent)

    # Production demandée :
    assert resultat["production"] == 600
    assert resultat["production_demandee"] == 600

    # Production de l'heure précédente
    assert resultat["production_precedente"] == 800

    # Limites techniques
    assert resultat["minimum_technique"] == 200
    assert resultat["maximum_technique"] == 1000

    assert resultat["minimum"] == 650
    assert resultat["maximum"] == 900

    # Valeurs des rampes
    assert resultat["rampe_montee"] == 100
    assert resultat["rampe_descente"] == 150

    # Identifiant de la centrale
    assert resultat["plant_id"] == "flamanville"