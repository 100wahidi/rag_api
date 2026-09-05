from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from modules.core.dependencies import get_compiler_engine
from modules.compiler.LatexCompiler import (
    LatexCompilationError,
    LatexCompiler,
    LatexTimeoutError,
)

MAX_LATEX_PAYLOAD_SIZE = 512 * 1024  # 512 KB
EXECUTION_TIMEOUT_SECONDS = 8.0

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


router = APIRouter(prefix="/v1/cv", tags=["CV Compiler"])


@router.post(
    "/compile",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}},
        400: {"description": "LaTeX Syntax Compilation Error"},
        413: {"description": "Payload Too Large"},
        500: {"description": "Internal Compiler Engine Failure"},
        504: {"description": "Compilation Timeout"},
    },
)
async def compile_latex_to_pdf(
    payload: LatexCompileRequest,
    compiler: Annotated[LatexCompiler, Depends(get_compiler_engine)],
):
    try:
        pdf_bytes = await compiler.compile(
            latex_source=payload.latex_source,
            timeout=EXECUTION_TIMEOUT_SECONDS,
        )
    except LatexTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        )
    except LatexCompilationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LaTeX compilation failed: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error processing LaTeX compilation.",
        ) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="compiled_cv.pdf"'},
    )