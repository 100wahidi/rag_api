import asyncio
from modules.compiler.LatexCompiler import LatexCompiler
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, validator

router = APIRouter(prefix="/compiler", tags=["LaTeX Compiler"])
MAX_LATEX_PAYLOAD_SIZE_BYTES = 512 * 1024  # 512 KB limit for CV source
COMPILATION_TIMEOUT_SECONDS = 8.0


class LatexCompileRequest(BaseModel):
    latex_source: str = Field(
        ...,
        min_length=10,
        max_length=MAX_LATEX_PAYLOAD_SIZE_BYTES,
        description="Raw LaTeX CV string payload",
    )

    @validator("latex_source")
    def validate_latex_source(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("LaTeX source must not be blank")
        if len(value.encode("utf-8")) > MAX_LATEX_PAYLOAD_SIZE_BYTES:
            raise ValueError("LaTeX source exceeds the 512 KB limit")
        return value


@router.post(
    "/compiler_endpoint",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}},
        400: {"description": "LaTeX Syntax Compilation Error"},
        413: {"description": "Payload Too Large"},
        504: {"description": "Compilation Timeout"},
    },
)
async def compile_latex_to_pdf(payload: LatexCompileRequest):
    compiler = LatexCompiler(payload.latex_source)
    try:
        pdf_bytes = await asyncio.wait_for(
            compiler.compile_to_pdf(payload.latex_source),
            timeout=COMPILATION_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="LaTeX compilation timed out") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="LaTeX compilation failed") from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="compiled_cv.pdf"'},
    )