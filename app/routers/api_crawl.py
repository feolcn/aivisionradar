from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import crawl_service, summary_service

router = APIRouter(prefix="/api/crawl", tags=["crawl"])


@router.post("/run")
def run_crawl(db: Session = Depends(get_db)):
    """Trigger a full crawl of all enabled sources."""
    result = crawl_service.crawl_all(db)
    return {"status": "ok", "result": result}


@router.post("/summarize")
async def run_summarize(db: Session = Depends(get_db)):
    """Summarize pending items with AI."""
    count = await summary_service.summarize_pending(db)
    return {"status": "ok", "summarized": count}
