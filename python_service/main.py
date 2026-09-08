from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from pathlib import Path
import logging
import json
from dijkstra.json_repository import JsonRepository
from dijkstra.region_service import RegionService
from simu_regionale import dashboard, conso_heure_region, perturber_consommation, repartition_par_heure, equilibrage_local_toutes_regions_nucleaires
from extraction_json import charger_donnees

class ConsoRegionRequest(BaseModel):
    id_region: str
    heure: str


class RepartitionHeureRequest(BaseModel):
    heure: str

class PerturbationRequest(BaseModel):
    id_region: str
    start: str
    end: str
    deltaMw: float 

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()
router = APIRouter()

app.include_router(router)

# Chemin vers le fichier JSON

DATA_FILE = Path(__file__).parent / "data" / "parc-nucleaire-prescriptif-france.json"

#Pour dijkstra
repository = JsonRepository(
    "data/parc-nucleaire-prescriptif-france.json"
)
region_service = RegionService(repository)




data = charger_donnees()

@app.get("/plants")
def get_plants():

    return {
        "count": len(data["parc_nucleaire"]["plants"]),
        "plants": [plant["name"] for plant in data["parc_nucleaire"]["plants"]]
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

@app.post("/conso_regionale_horaire")
def conso_regionale_horaire(payload: ConsoRegionRequest):
    try:
        return conso_heure_region(payload.id_region, payload.heure)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@app.post("/repartition_heure")
def repartition_heure(request: RepartitionHeureRequest):

    logger.info(f"Demande de répartition horaire - Heure: {request.heure}")

    resultat_global = equilibrage_local_toutes_regions_nucleaires()
    prod_reelle = resultat_global["prod_reelle"]

    repartition = repartition_par_heure(prod_reelle, request.heure)
    

    if not repartition:
        logger.warning(f"Aucune donnée de production trouvée pour l'heure : {request.heure}")
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": f"Aucune donnée de production pour l'heure '{request.heure}'"
            }
        )

    return {
        "success": True,
        "heure": request.heure,
        "resultats": repartition
    }

@app.get("/repartition")
def get_repartition():
   result = equilibrage_local_toutes_regions_nucleaires()
   repartition = result["prod_reelle"]
   return repartition

@app.post("/perturber_consommation")
def perturbation(id_region, start, end, deltaMw):
    try:
        result =  equilibrage_local_toutes_regions_nucleaires(id_region, start, end, deltaMw)
        return result["details_regionaux"], result["energie_non_fournie"], result["energie_a_revendre"]
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
