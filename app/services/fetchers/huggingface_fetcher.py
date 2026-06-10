import logging
from sqlalchemy.orm import Session
from app.models import Source
from app.services.fetchers.rss_fetcher import fetch_rss

logger = logging.getLogger(__name__)


def fetch_huggingface(db: Session, source: Source) -> int:
    """Hugging Face Blog and Daily Papers both offer RSS feeds."""
    return fetch_rss(db, source)
