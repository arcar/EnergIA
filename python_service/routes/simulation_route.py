from fastapi import APIRouter, HTTPException
from models.simulation import SimulationRequest, RepartitionHeureRequest
from simu_regionale import (
    repartition_par_heure,
    equilibrage_local_toutes_regions_nucleaires,
)
from services.simulation_service import simuler_augmentation
from dijkstra.json_repository import JsonRepository
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


repository = JsonRepository(
    "data/parc-nucleaire-prescriptif-france.json"
)

@router.post("/repartition_heure")
def repartition_heure(request: RepartitionHeureRequest):

    logger.info(
        f"Demande de répartition horaire - Heure: {request.heure}"
    )

    resultat_global = equilibrage_local_toutes_regions_nucleaires()
    prod_reelle = resultat_global["prod_reelle"]

    repartition = repartition_par_heure(prod_reelle, request.heure)

    if not repartition:
        logger.warning(
            f"Aucune donnée de production trouvée pour l'heure : {request.heure}"
        )
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
        "resultats": repartition,
    }

@router.post("/simulation")
def simulation(request: SimulationRequest):

    logger.info(
        f"Nouvelle simulation demandée - Région: {request.region}, Augmentation: {request.augmentation} MW"
    )

    # Vérification région

    regions = repository.get_regions()

    logger.info(
        f"Vérification de la région : {request.region}"
    )

    region_existante = next(
        (
            r for r in regions
            if r["id"].lower() == request.region.lower()
        ),
        None
    )


    if region_existante is None:
        
        logger.warning(
            f"Tentative de simulation avec une région inconnue : {request.region}"
        )

        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": f"La région '{request.region}' n'existe pas"
            }
        )


    return simuler_augmentation(
        request.region,
        request.augmentation
    )