from fastapi import FastAPI
from pathlib import Path
from pydantic import BaseModel
import json

from dijkstra.dijkstra_service import DijkstraService



app = FastAPI()


# Chemin vers le fichier JSON

DATA_FILE = Path(__file__).parent / "data" / "parc-nucleaire-prescriptif-france.json"


# Initialisation Dijkstra

dijkstra_service = DijkstraService(DATA_FILE)


# Chargement JSON pour /plants

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)



@app.get("/plants")
def get_plants():

    return {
        "count": len(data["plants"]),
        "plants": [
            plant["name"]
            for plant in data["plants"]
        ]
    }



# Modèle de requête pour Dijkstra

class PathRequest(BaseModel):

    start: str
    goal: str
    weight: str = "distance"



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
