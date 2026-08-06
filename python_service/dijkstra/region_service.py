from dijkstra.graph_builder import GraphBuilder
from dijkstra.dijkstra_service import DijkstraService


class RegionService:

    def __init__(self, repository):

        self.repository = repository

        data = repository.load()

        self.graph = GraphBuilder(data).build()

        self.dijkstra = DijkstraService(self.graph)

    def compute_routes(self, region_id):

        data = self.repository.load()

        region = next(

            (
                r
                for r in data["regions"]
                if r["name"] == region_id
            ),
            None
        )

        if region is None:
            raise ValueError("Region inconnue")

        if len(region["local_plant_ids"]) == 0:
            raise ValueError(
                "Cette région ne possède aucune centrale locale."
            )

        source = region["local_plant_ids"][0]

        routes = self.dijkstra.shortest_paths(source)

        return {

            "region": region["name"],

            "source_plant": source,

            "routes": routes

        }