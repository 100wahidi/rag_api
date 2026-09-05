from modules.compiler.LatexCompiler import LatexCompiler
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

router = APIRouter("compiler")
MAX_LATEX_PAYLOAD_SIZE_BYTES = 512 * 1024  # 512 KB limit for CV source
COMPILATION_TIMEOUT_SECONDS = 8.0


class LatexCompileRequest(BaseModel):
    latex_source: str = Field(
        ...,
        min_length=10,
        max_length=MAX_LATEX_PAYLOAD_SIZE_BYTES,
        description="Raw LaTeX CV string payload",
    )


@router.post(
    "/v1/cv/compile-pdf",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}},
        400: {"description": "LaTeX Syntax Compilation Error"},
        413: {"description": "Payload Too Large"},
        504: {"description": "Compilation Timeout"},
    },
)
async def compile_latex_to_pdf(payload: LatexCompileRequest):
    compiler = LatexCompiler()
    pdf_bytes = await compiler.compile_to_pdf(payload.latex_source)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="compiled_cv.pdf"'},
    )