import logging

from sqlalchemy.orm import Session

from app.models import Source
from app.services.fetchers.rss_fetcher import fetch_rss

logger = logging.getLogger(__name__)


def fetch_arxiv(db: Session, source: Source) -> int:
    """arXiv RSS is standard RSS, delegate to RSS fetcher."""
    return fetch_rss(db, source)
