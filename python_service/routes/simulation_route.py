from fastapi import APIRouter
from models.simulation import SimulationRequest


router = APIRouter()


@router.post("/simulation")
def simulation(request: SimulationRequest):

    return {
        "success": True,
        "centrales": [
            {
                "nom": "Paluel",
                "puissance": 300
            }
        ]
    }