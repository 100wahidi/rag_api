from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, field_validator




MAX_LATEX_PAYLOAD_SIZE = 512 * 1024  # 512 KB


class LatexCompileRequest(BaseModel):
    latex_source: str = Field(..., min_length=10)

class LatexCompileRequest(BaseModel):
    latex_source: str = Field(
        ...,
        min_length=10,
        max_length=MAX_LATEX_PAYLOAD_SIZE,
        description="Raw LaTeX source string.",
    )

    @field_validator("latex_source")
    @classmethod
    def validate_primitives(cls, value: str) -> str:
        forbidden = (r"\write18", r"\input", r"\include", r"\openout")
        if any(token in value for token in forbidden):
            raise ValueError("Payload contains forbidden LaTeX macros/primitives.")
        return value
