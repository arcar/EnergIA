from graph import load_data, build_graph

def test_graph_creation():

    data = load_data("../data/parc-nucleaire-prescriptif-france.json")

    graph = build_graph(data)

    assert "belleville" in graph

    assert len(graph["belleville"]) > 0