from .dijkstra_service import DijkstraService


def test_service_creation():

    service = DijkstraService(
        "../data/parc-nucleaire-prescriptif-france.json"
    )

    assert service.graph is not None