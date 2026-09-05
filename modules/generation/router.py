from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from modules.core.dependencies import get_db
from modules.authentication.service import get_current_user
from .generation import GenerationService
from .schema import RAGGenerationPayload
from typing import Annotated
from modules.core.logs import setup_logger
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from modules.core.dependencies import get_compiler_engine
from modules.generation.LatexCompiler import (
    LatexCompilationError,
    LatexCompiler,
    LatexTimeoutError,
)


EXECUTION_TIMEOUT_SECONDS = 8.0

logger = setup_logger(__name__)

router = APIRouter(prefix="/generation", tags=["retrival augmented generation"])

async def get_service(request:Request):
    generation_service = request.app.state.generation_model
    return generation_service

@router.post("/get_cv")
async def upload_file(
    request: Request,
    generation_payload: RAGGenerationPayload,
    compiler: Annotated[LatexCompiler, Depends(get_compiler_engine)],
    session: Annotated[AsyncSession, Depends(get_db)],
    username: str = Depends(get_current_user)
):  
    # Access the generation model from the FastAPI app state
    Client_llm = await get_service(request)
    print(Client_llm.handlel_llm())
    # since mistral llm is async, we can call it directly without blocking the event loop
    latex_cv = await GenerationService(
        Client=Client_llm,
    ).generate_cv(username, session, generation_payload.offer_extraction,generation_payload.best_experiences, generation_payload.best_projects)

    try:
        pdf_bytes = await compiler.compile(
            latex_source=latex_cv.latex_source,
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
    







