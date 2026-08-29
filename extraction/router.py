from fastapi import APIRouter
from fastapi import Depends, HTTPException
from authentication.service import get_current_user
from .extraction import ExtractionService
from core.security import Settings
from core.logs import setup_logger

logger = setup_logger(__name__)
settings = Settings()

router = APIRouter(prefix="/rag", tags=["retrival augmented generation"])
             
      
@router.post("/rag/extraction")
async def process_offer(offer_passage: str, username: str = Depends(get_current_user)):

    try:
        text_extraction = ExtractionService(api_key=settings.MISTRAL_API_KEY).extract(offer_passage)
    except Exception:
        logger.exception("Offer parsing failure")
        raise HTTPException(status_code=503,detail="Parser unavailable")

    if not text_extraction:
        raise HTTPException(status_code=400,detail="Unable to parse offer")
    logger.info("Offer successfully parsed user=%s",username)
    return {"username": username,"offer_key_insights": text_extraction}

