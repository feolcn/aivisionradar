from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import crawl_service, summary_service

router = APIRouter(tags=["crawl"])


@router.post("/api/crawl/run")
def run_crawl(db: Session = Depends(get_db)):
    """Trigger a full crawl of all enabled sources."""
    result = crawl_service.crawl_all(db)
    return {"status": "ok", "result": result}


@router.post("/api/crawl/summarize")
async def run_summarize(db: Session = Depends(get_db)):
    """Summarize pending items with AI."""
    count = await summary_service.summarize_pending(db)
    return {"status": "ok", "summarized": count}


@router.post("/api/translate/run")
async def run_translate(db: Session = Depends(get_db)):
    """Translate pending items to Chinese."""
    if not summary_service.is_translation_enabled(db):
        return {"status": "skipped", "reason": "翻译未开启，请在设置页面开启"}
    count = await summary_service.translate_pending(db, limit=50)
    return {"status": "ok", "translated": count, "message": f"已翻译 {count} 条内容"}
