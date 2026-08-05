from .graph import load_data, build_graph
from .dijkstra import dijkstra


class DijkstraService:

    def __init__(self, json_path):
        data = load_data(json_path)
        self.graph = build_graph(data)

    def shortest_path(self, start, goal, weight="distance"):
        return dijkstra(self.graph, start, goal, weight)

    def shortest_distance(self, start, goal):
        result = self.shortest_path(start, goal)
        if result is None:
            return None
        return result["distance_km"]

    def path_exists(self, start, goal):
        return self.shortest_path(start, goal) is not None

    def neighbors(self, node):
        return self.graph.get(node, [])

    def path_capacity(self, path):

        max_capacity = float("inf")

        for i in range(len(path) - 1):

            source = path[i]
            destination = path[i + 1]

            for edge in self.graph[source]:

                if edge["node"] == destination:

                    max_capacity = min(
                        max_capacity,
                        edge["capacity"]
                    )

                    break

        return max_capacity

