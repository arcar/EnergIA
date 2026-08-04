from dijkstra_service import DijkstraService
from dispatch_service import DispatchService


def test_dispatch():

    dijkstra = DijkstraService(
        "../data/parc-nucleaire-prescriptif-france.json"
    )


    dispatch = DispatchService(
        "../data/parc-nucleaire-prescriptif-france.json",
        dijkstra
    )


    result = dispatch.allocate_power(
        "belleville",
        500
    )

    def test_rank_candidates():

        dijkstra = DijkstraService(
            "../data/parc-nucleaire-prescriptif-france.json"
        )

        dispatch = DispatchService(
            "../data/parc-nucleaire-prescriptif-france.json",
            dijkstra
        )

        candidates = dispatch.rank_candidates(
            "belleville"
        )

        assert len(candidates) > 0

        print(candidates)



    print(result)


    assert result["allocated_power_mw"] > 0

def test_dispatch_status():

    dijkstra = DijkstraService(
        "../data/parc-nucleaire-prescriptif-france.json"
    )

    dispatch = DispatchService(
        "../data/parc-nucleaire-prescriptif-france.json",
        dijkstra
    )

    result = dispatch.allocate_power(
        "belleville",
        500
    )

    assert result["status"] in [
        "satisfied",
        "partially_satisfied"
    ]
def test_path_capacity():

    service = DijkstraService(
        "../data/parc-nucleaire-prescriptif-france.json"
    )

    capacity = service.path_capacity(
        [
            "flamanville",
            "chinon",
            "saint_laurent",
            "belleville"
        ]
    )

    assert capacity > 0

    print("capacity:", capacity)

def test_local_region_filter():

    dijkstra = DijkstraService(
        "../data/parc-nucleaire-prescriptif-france.json"
    )

    dispatch = DispatchService(
        "../data/parc-nucleaire-prescriptif-france.json",
        dijkstra
    )

    plants = dispatch.plants_by_region(
        "Centre-Val de Loire",
        "belleville"
    )

    assert len(plants) > 0

    print(plants)


def test_remaining_power():

    dijkstra = DijkstraService(
        "../data/parc-nucleaire-prescriptif-france.json"
    )

    dispatch = DispatchService(
        "../data/parc-nucleaire-prescriptif-france.json",
        dijkstra
    )

    result = dispatch.allocate_power(
        "belleville",
        500
    )

    assert result["requested_power_mw"] == 500

    assert (
        result["allocated_power_mw"]
        +
        result["remaining_power_mw"]
        ==
        result["requested_power_mw"]
    )



