from fastapi import FastAPI
from pathlib import Path
from routes import simulation_route
import json

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



@app.get("/plants")
def get_plants():

    return {
        "count": len(data["plants"]),
        "plants": [plant["name"] for plant in data["plants"]]
    }

