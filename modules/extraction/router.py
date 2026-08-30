from fastapi import APIRouter
from fastapi import Depends, HTTPException
from modules.authentication.service import get_current_user
from modules.extraction.extraction import ExtractionService
from modules.core.security import Settings
from modules.core.logs import setup_logger

logger = setup_logger(__name__)
settings = Settings()

router = APIRouter(prefix="/extraction", tags=["retrival augmented generation"])



@router.post("/offer_extraction")
async def process_offer(offer_passage: str, username: str = Depends(get_current_user)):
    try:
        text_extraction = ExtractionService(api_key=settings.MISTRAL_API_KEY).extract(offer_passage)
    except Exception  as exp:
        logger.error("Error occurred while extracting text: %s", exp)
        raise HTTPException(status_code=503,detail="Extraction service unavailable")
    
    logger.info("Offer successfully parsed user=%s",username)
    return {"username": username,"offer_key_insights": text_extraction}

