from pydantic import BaseModel, Field


class LatexCompileRequest(BaseModel):
    latex_source: str = Field(..., min_length=10)
