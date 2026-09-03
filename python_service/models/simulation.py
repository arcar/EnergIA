from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):

    region: str

    augmentation: float = Field(
        gt=0,
        description="L'augmentation de consommation doit être supérieure à 0 MW"
    )

class RepartitionHeureRequest(BaseModel):
    heure: str