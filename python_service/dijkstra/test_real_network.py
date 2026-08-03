from graph import load_data, build_graph
from dijkstra import dijkstra


def test_real_network_path():

    data = load_data("../../data/parc-nucleaire-prescriptif-france.json")

    graph = build_graph(data)
    result = dijkstra(graph, "flamanville", "tricastin")

    print(result)

    assert result is not None

    assert result["path"][0] == "flamanville"

    assert result["path"][-1] == "tricastin"

    assert result["distance_km"] > 0