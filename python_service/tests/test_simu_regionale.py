from simu_regionale import demande_moins_non_pilotable
from unittest.mock import patch

def test_demande_moins_non_pilotable():
    consommation = {
        "normandie": [2000, 2200, 1800],
        "bretagne": [1500, 1600, 1400]
    }

    production_non_pilotable = {
        "normandie": [500, 600, 400],
        "bretagne": [300, 400, 200]
    }

    resultat_attendu = {
        "normandie": [1500, 1600, 1400],
        "bretagne": [1200, 1200, 1200]
    }

    with patch(
        "simu_regionale.demande_regionale",
        return_value=consommation
    ), patch(
        "simu_regionale.production_non_pilotables_regional",
        return_value=production_non_pilotable
    ):

        resultat = demande_moins_non_pilotable()

    assert resultat == resultat_attendu
