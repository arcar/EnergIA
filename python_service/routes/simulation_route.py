from fastapi import APIRouter, HTTPException
from models.simulation import SimulationRequest
from services.simulation_service import simuler_augmentation
from dijkstra.json_repository import JsonRepository
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


repository = JsonRepository(
    "data/parc-nucleaire-prescriptif-france.json"
)


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