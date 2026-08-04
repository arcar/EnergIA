from pydantic import BaseModel


class SimulationRequest(BaseModel):
    region: str
    augmentation: float