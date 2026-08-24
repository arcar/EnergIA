import heapq
from math import inf


class DijkstraService:

    def __init__(self, graph):
        self.graph = graph

    def shortest_paths(self, start):

        distances = {
            node: inf
            for node in self.graph
        }

        losses = {
            node: 0
            for node in self.graph
        }

        capacities = {
            node: None
            for node in self.graph
        }

        paths = {
            node: []
            for node in self.graph
        }

        distances[start] = 0
        paths[start] = [start]

        priority_queue = [
            (0, start)
        ]

        while priority_queue:

            current_distance, current_node = heapq.heappop(
                priority_queue
            )

            if current_distance > distances[current_node]:
                continue

            for edge in self.graph[current_node]:

                neighbor = edge["to"]

                new_distance = (
                    current_distance
                    + edge["distance"]
                )

                if new_distance < distances[neighbor]:

                    distances[neighbor] = new_distance

                    losses[neighbor] = (
                        losses[current_node]
                        + edge["loss"]
                    )

                    if capacities[current_node] is None:

                        capacities[neighbor] = edge["capacity"]

                    else:

                        capacities[neighbor] = min(
                            capacities[current_node],
                            edge["capacity"]
                        )

                    paths[neighbor] = (
                        paths[current_node]
                        + [neighbor]
                    )

                    heapq.heappush(
                        priority_queue,
                        (
                            new_distance,
                            neighbor
                        )
                    )

        result = {}

        for node in self.graph:

            if distances[node] == inf:
                continue

            result[node] = {

                "path": paths[node],

                "distance_km": round(
                    distances[node],
                    2
                ),

                "total_loss_percent": round(
                    losses[node],
                    2
                ),

                "max_transfer_mw": capacities[node]

            }

        return result