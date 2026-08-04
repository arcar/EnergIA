from fastapi import FastAPI
from pathlib import Path
from routes import simulation_route
import json
from pydantic import BaseModel
from dijkstra.dijkstra_service import DijkstraService



app = FastAPI()

app.include_router(simulation_route.router)

# Chemin vers le fichier JSON

DATA_FILE = Path(__file__).parent / "data" / "parc-nucleaire-prescriptif-france.json"


# Initialisation Dijkstra

dijkstra_service = DijkstraService(DATA_FILE)


# Chargement JSON pour /plants

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

class PathRequest(BaseModel):
    start: str
    goal: str
    weight: str = "distance"


@app.get("/plants")
def get_plants():

    return {
        "count": len(data["plants"]),
        "plants": [plant["name"] for plant in data["plants"]]
    }

@app.post("/shortest_path")
def shortest_path(request: PathRequest):

    result = dijkstra_service.shortest_path(
        start=request.start,
        goal=request.goal,
        weight=request.weight
    )

    if result is None:
        return {
            "status": "no_path",
            "start": request.start,
            "goal": request.goal
        }

    return {
        "status": "success",
        "result": result
    }