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
    latex_source: str 

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
    if not await compiler.resolve_tex_engine():
        raise HTTPException(status_code=400, detail="Failed to resolve LaTeX engine")
    
    try:
        pdf_bytes = await asyncio.wait_for(
            compiler.compile_to_pdf(),
            timeout=COMPILATION_TIMEOUT_SECONDS
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