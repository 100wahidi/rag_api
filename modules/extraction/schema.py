from pydantic import BaseModel, Field



class ExtractionInput(BaseModel):
    offer: str = Field(..., description="Job offer text to extract experiences and projects from")

