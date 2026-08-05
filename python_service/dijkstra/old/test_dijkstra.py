from python_service.dijkstra.old.dijkstra import dijkstra


def test_simple_path():

    graph = {

        "A": [
            {
                "node": "B",
                "distance": 10,
                "capacity": 100
            }
        ],

        "B": [
            {
                "node": "C",
                "distance": 20,
                "capacity": 100
            }
        ],

        "C": []

    }

    result = dijkstra(graph, "A", "C")

    assert result["path"] == [
        "A",
        "B",
        "C"
    ]

    assert result["distance_km"] == 30


def test_no_path():

    graph = {

        "A": [
            {
                "node": "B",
                "distance": 10,
                "capacity": 100
            }
        ],

        "B": [],

        "C": []

    }

    result = dijkstra(graph, "A", "C")

    assert result is None


def test_shortest_path():

    graph = {

        "A": [
            {
                "node": "B",
                "distance": 10,
                "capacity": 100
            },
            {
                "node": "C",
                "distance": 5,
                "capacity": 100
            }
        ],

        "B": [
            {
                "node": "D",
                "distance": 10,
                "capacity": 100
            }
        ],

        "C": [
            {
                "node": "D",
                "distance": 30,
                "capacity": 100
            }
        ],

        "D": []

    }

    result = dijkstra(graph, "A", "D")

    assert result["path"] == [
        "A",
        "B",
        "D"
    ]

    assert result["distance_km"] == 20

def test_path_information():

    graph = {

        "A": [
            {
                "node":"B",
                "distance":100,
                "loss":2,
                "capacity":500
            }
        ],

        "B":[]

    }


    result = dijkstra(
        graph,
        "A",
        "B"
    )


    assert result["distance_km"] == 100
    assert result["loss_percent"] == 2
    assert result["max_capacity_mw"] == 500