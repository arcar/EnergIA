from dijkstra.graph_builder import GraphBuilder
from dijkstra.dijkstra_service import DijkstraService
import unicodedata



def normaliser_region(region):
    region = region.lower().strip()

    region = unicodedata.normalize("NFD", region)
    region = "".join(
        caractere
        for caractere in region
        if unicodedata.category(caractere) != "Mn"
    )

    region = region.replace("-", "_").replace(" ", "_")

    return region

class RegionService:

    def __init__(self, repository):

        self.repository = repository

        data = repository.load()

        self.graph = GraphBuilder(data).build()

        self.dijkstra = DijkstraService(self.graph)

    def compute_routes(self, region_id):

        region_id = normaliser_region(region_id)

        data = self.repository.load()

        region = next(

            (
                r
                for r in data["regions"]
                if r["id"] == region_id
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