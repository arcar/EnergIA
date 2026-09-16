from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from pathlib import Path
import logging
import json
from fastapi.middleware.cors import CORSMiddleware
from dijkstra.json_repository import JsonRepository
from dijkstra.region_service import RegionService
from simu_regionale import dashboard, conso_heure_region, perturber_consommation, reinitialiser_scenario, repartition_par_heure, equilibrage_local_toutes_regions_nucleaires
from extraction_json import charger_donnees
from simu_regionale_predict import (dashboard_predict, perturber_consommation_predict, repartition_par_heure as repartition_par_heure_predict, equilibrage_local_toutes_regions_nucleaires_predict, obtenir_prediction_consommation, construire_etats_dashboard_predict)
class ConsoRegionRequest(BaseModel):
    id_region: str
    heure: str

class PredictionConsoRequest(BaseModel):
    id_region: str
    date: str
    heure: str

class RepartitionHeureRequest(BaseModel):
    heure: str

class PerturbationRequest(BaseModel):
    id_region: str
    date_debut: str
    heure_debut: str
    date_fin: str
    heure_fin: str
    deltaMw: float

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class RepartitionHeurePredictRequest(BaseModel):
    date: str
    heure: str

app = FastAPI()
router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/health")
def health():
    return {"status": "ok"}

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
def perturbation(request:PerturbationRequest):
    try:
        return dashboard(request.id_region,request.start,request.end,request.deltaMw)
    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e))
    
@app.post("/reinitialiser_scenario")
def route_reinitialiser_scenario():
    return reinitialiser_scenario()

#================================
# Predictions
#================================

@app.get("/predict/dashboard")
def get_dashboard_predict():
    return dashboard_predict()

@app.post("/predict/conso_regionale")
def prediction_conso_regionale(request: PredictionConsoRequest):
    try:
        return obtenir_prediction_consommation(
            request.id_region,
            request.date,
            request.heure
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/predict/repartition_heure")
def repartition_heure_predict(request: RepartitionHeurePredictRequest):

    label = f"{request.date} {request.heure}"
    logger.info(f"Demande de répartition horaire (prévisions) - {label}")

    resultat_global = equilibrage_local_toutes_regions_nucleaires_predict()
    prod_reelle = resultat_global["prod_reelle"]

    repartition = repartition_par_heure_predict(prod_reelle, label)

    if not repartition:
        logger.warning(f"Aucune donnée de production trouvée pour : {label}")
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": f"Aucune donnée de production pour '{label}'"
            }
        )

    return {
        "success": True,
        "date": request.date,
        "heure": request.heure,
        "resultats": repartition
    }


@app.get("/predict/repartition")
def get_repartition_predict():
    result = equilibrage_local_toutes_regions_nucleaires_predict()
    return result["prod_reelle"]


@app.post("/predict/perturber_consommation")
def perturbation_predict(request: PerturbationRequest):
    try:

        # 1. Enregistrer la perturbation
        scenario = perturber_consommation_predict(
            request.id_region,
            request.date_debut,
            request.heure_debut,
            request.date_fin,
            request.heure_fin,
            request.deltaMw
        )

        # 2. Calculer uniquement la période perturbée
        result = equilibrage_local_toutes_regions_nucleaires_predict(
            date_debut=request.date_debut,
            heure_debut=request.heure_debut,
            date_fin=request.date_fin,
            heure_fin=request.heure_fin
        )

        return {
             "scenarios_actifs": scenario["scenarios_actifs"],
            "perturbation": {
                "region": request.id_region,
                "date_debut": request.date_debut,
                "heure_debut": request.heure_debut,
                "date_fin": request.date_fin,
                "heure_fin": request.heure_fin,
                "deltaMw": request.deltaMw
            },
            "resultats": construire_etats_dashboard_predict(result)
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
