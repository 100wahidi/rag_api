from fastapi import APIRouter, Request
from fastapi import Depends, HTTPException
from modules.authentication.service import get_current_user
from modules.extraction.extraction import ExtractionService
from modules.extraction.schema import ExtractionInput
from modules.core.security import Settings
from modules.core.logs import setup_logger

logger = setup_logger(__name__)
settings = Settings()

router = APIRouter(prefix="/extraction", tags=["retrival augmented generation"])


async def get_service(request:Request):
    generation_service = request.app.state.generation_model
    return generation_service

@router.post("/offer_extraction")
async def process_offer(extraction_input: ExtractionInput, request: Request, username: str = Depends(get_current_user)):

    Client = await get_service(request)
    try:
        text_extraction = await ExtractionService(client=Client).extract(extraction_input.offer)
    except Exception  as exp:
        logger.error("Error occurred while extracting text: %s", exp)
        raise HTTPException(status_code=503,detail="Extraction service unavailable")
    
    logger.info("Offer successfully parsed user=%s",username)
    return {"username": username,"offer_key_insights": text_extraction}

