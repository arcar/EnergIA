from metrique_centrale import get_puissance_disponible, get_centrale_disponible, get_taux_saturation, get_nom_region, get_central_id, get_centrale_regionale, calcul_demande_residuelle

from unittest.mock import patch

def test_get_puissance_disponible():
    centrale = {
        "simulation": {
            "soft_upper_bound_mw": 5054,
            "initial_output_mw": 4400
        }
    }

    resultat = get_puissance_disponible(centrale)

    assert resultat == 654


def test_get_puissance_disponible():
    centrale = {
        "simulation": {
            "soft_upper_bound_mw": 5054,
            "initial_output_mw": 4400
        }
    }

    resultat = get_puissance_disponible(centrale)

    assert resultat == 654


def test_get_centrale_disponible():
    centrale = {
        "simulation": {
            "available": True
        }
    }

    resultat = get_centrale_disponible(centrale)

    assert resultat is True

def test_get_taux_saturation():
    centrale = {
        "simulation": {
            "soft_upper_bound_ratio": 0.95
        }
    }

    resultat = get_taux_saturation(centrale)

    assert resultat == 0.95

def test_get_nom_region():
    centrale = {
        "location": {
            "region_id": "ile_de_france"
        }
    }

    resultat = get_nom_region(centrale)

    assert resultat == "ile_de_france"

def test_get_central_id():
    centrale = {
        "id": "flamanville"
    }

    resultat = get_central_id(centrale)

    assert resultat == "flamanville"

def test_get_centrale_regionale():
    metriques = [
        {
            "central_id": "flamanville",
            "region": "normandie",
            "puissance_disponible": 576,
            "taux_saturation": 0.95,
            "disponible": True
        },
        {
            "central_id": "paluel",
            "region": "normandie",
            "puissance_disponible": 654,
            "taux_saturation": 0.95,
            "disponible": True
        },
        {
            "central_id": "nogent",
            "region": "ile_de_france",
            "puissance_disponible": 289,
            "taux_saturation": 0.95,
            "disponible": True
        }
    ]

    with patch("metrique_centrale.get_metrique_centrale", return_value=metriques):
        resultat = get_centrale_regionale("normandie")

    assert len(resultat) == 2
    assert resultat[0]["central_id"] == "flamanville"
    assert resultat[1]["central_id"] == "paluel"

def test_calcul_demande_residuelle():
    centrales = [
        {
            "central_id": "flamanville",
            "region": "normandie",
            "puissance_disponible": 576,
            "taux_saturation": 0.95,
            "disponible": True
        },
        {
            "central_id": "paluel",
            "region": "normandie",
            "puissance_disponible": 654,
            "taux_saturation": 0.95,
            "disponible": True
        },
        {
            "central_id": "penly",
            "region": "normandie",
            "puissance_disponible": 330,
            "taux_saturation": 0.95,
            "disponible": True
        }
    ]

    with patch(
        "metrique_centrale.get_centrale_regionale",
        return_value=centrales
    ):
        resultat, puissance_disponible_regional = calcul_demande_residuelle(2000, "normandie")

    assert resultat == 440
    assert puissance_disponible_regional == 1560