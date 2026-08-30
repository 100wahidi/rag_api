from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlmodel import select
from modules.core.database import Alice
from modules.core.dependencies import get_db
from modules.authentication.service import get_current_user
from modules.injection.schema import (
    ExtractionResponse,
    BulkInsertionPayload,
    ExtractionLLMResponse,
)
from modules.injection.extraction import InjectionService, async_persist_task

router = APIRouter(prefix="/extraction", tags=["Extraction & Ingestion"])


@router.post("/process-cv", response_model=ExtractionResponse, status_code=status.HTTP_200_OK)
async def process_cv_and_extract(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_persist: bool = True,
    username = Depends(get_current_user),
    session=Depends(get_db)
):
    """Parses PDF text, extracts experiences & projects via LLM, and asynchronously writes to DB."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported for CV extraction.",
        )
    result = await session.execute(select(Alice).where(Alice.name == f'{username}'))
    user = result.scalar_one_or_none()
    file_bytes = await file.read()
    llm_client = request.app.state.generation_model
    raw_text = await InjectionService(llm_client).extract_text_from_pdf(file_bytes)

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to extract text from the uploaded PDF document.",
        )

    # 1. LLM Structured Extraction
    extracted_data: ExtractionLLMResponse = await InjectionService(llm_client).extract_entities_with_llm(raw_text)

    # 2. Async persistence if flag is set
    if auto_persist:
        background_tasks.add_task(
            async_persist_task,
            session,
            user_id=user.user_id,
            experiences=[item.model_dump() for item in extracted_data.experiences],
            projects=[item.model_dump() for item in extracted_data.projects],
        )

    return ExtractionResponse(
        status="processed_and_queued" if auto_persist else "extracted",
        experiences_count=len(extracted_data.experiences),
        projects_count=len(extracted_data.projects),
        data=extracted_data,
    )


@router.post("/insert-manual", status_code=status.HTTP_201_CREATED)
async def insert_manual_records(
    payload: BulkInsertionPayload,
    session: Session = Depends(get_db),
    username = Depends(get_current_user),
):
    """Directly insert a list of experiences and projects (e.g. from frontend form inputs)."""
    result = await session.execute(select(Alice).where(Alice.name == f'{username}'))
    user = result.scalar_one_or_none()

    result = InjectionService.insert_extracted_records(
        session=session,
        user_id=user.user_id,
        experiences=payload.experiences,
        projects=payload.projects,
    )
    return {
        "status": "success",
        "message": "Records successfully inserted.",
        "details": result,
    }