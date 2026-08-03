from fastapi import FastAPI
from pathlib import Path
import json

app = FastAPI()

# Chemin vers le fichier JSON

DATA_FILE = Path(__file__).parent / "data" / "parc-nucleaire-prescriptif-france.json"


with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


@app.get("/plants")
def get_plants():
    return {
        "count": len(data["plants"]),
        "plants": [plant["name"] for plant in data["plants"]]
    }