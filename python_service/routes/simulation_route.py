from fastapi import APIRouter
from models.simulation import SimulationRequest


router = APIRouter()


from services.simulation_service import simuler_augmentation



@router.post("/simulation")
def simulation(request: SimulationRequest):

    return simuler_augmentation(
        request.region,
        request.augmentation
    )