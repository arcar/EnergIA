from collections import defaultdict


class GraphBuilder:

    def __init__(self, data):
        self.data = data

    def build(self):

        graph = defaultdict(list)

        for edge in self.data["plant_edges"]:

            source = edge["from"]
            destination = edge["to"]

            distance = edge["geodesic_distance_km"]
            loss = edge["estimated_loss_percent"]
            capacity = edge["max_transfer_mw"]

            graph[source].append(
                {
                    "to": destination,
                    "distance": distance,
                    "loss": loss,
                    "capacity": capacity
                }
            )

            # graphe non orienté
            graph[destination].append(
                {
                    "to": source,
                    "distance": distance,
                    "loss": loss,
                    "capacity": capacity
                }
            )

        return dict(graph)