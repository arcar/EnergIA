import json


def load_data(path: str):
    #Charge le fichier JSON contenant les données 

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_graph(data: dict):
    #Construit un graphe à partir de la section plant_edges du JSON

    graph = {}

    for edge in data["plant_edges"]:

        # Ignore les liaisons indisponibles
        if not edge["available"]:
            continue

        source = edge["from"]
        target = edge["to"]

        graph.setdefault(source, [])
        graph.setdefault(target, [])

        graph[source].append({
            "node": target,
            "distance": edge["geodesic_distance_km"],
            "loss": edge["estimated_loss_percent"],
            "capacity": edge["max_transfer_mw"]
        })

        if edge["bidirectional"]:
            graph[target].append({
                "node": source,
                "distance": edge["geodesic_distance_km"],
                "loss": edge["estimated_loss_percent"],
                "capacity": edge["max_transfer_mw"]
            })

    return graph


if __name__ == "__main__":

    data = load_data("../data/parc-nucleaire-prescriptif-france.json")

    graph = build_graph(data)

    print(graph["belleville"])