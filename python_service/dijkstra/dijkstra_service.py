from graph import load_data, build_graph
from dijkstra import dijkstra


class NetworkService:

    def __init__(self, json_path):

        data = load_data(json_path)

        self.graph = build_graph(data)

    def shortest_path(self, start, goal, weight="distance"):

        return dijkstra(
            self.graph,
            start,
            goal,
            weight
        )