from fastapi import FastAPI, HTTPException
from pathlib import Path
from routes import simulation_route
import json
from dijkstra.json_repository import JsonRepository
from dijkstra.region_service import RegionService
import logging
from simu_regionale import dashboard


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()

app.include_router(simulation_route.router)

# Chemin vers le fichier JSON

DATA_FILE = Path(__file__).parent / "data" / "parc-nucleaire-prescriptif-france.json"

#Pour dijkstra
repository = JsonRepository(
    "data/parc-nucleaire-prescriptif-france.json"
)
region_service = RegionService(repository)

# Chargement JSON pour /plants

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

@app.get("/plants")
def get_plants():

    return {
        "count": len(data["plants"]),
        "plants": [plant["name"] for plant in data["plants"]]
    }


@app.get("/regions")
def get_regions():
   return repository.get_regions()


@app.get("/routes/{region_id}")
def get_region(region_id: str):

    regions = repository.get_regions()

    region = next(
        (r for r in regions if r["id"] == region_id),
        None
    )

    if region is None:
        raise HTTPException(
            status_code=404,
            detail="Région inconnue"
        )

    return region


@app.get("/regions/routes/{region_id}")
def compute_routes(region_id: str):

    try:

        return region_service.compute_routes(region_id)

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@app.get("/dashboard")
def get_dashboard():
    return dashboard()