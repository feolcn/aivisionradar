import logging

from sqlalchemy.orm import Session

from app.models import Source
from app.services import scoring_service
from app.services.fetchers.arxiv_fetcher import fetch_arxiv
from app.services.fetchers.github_search_fetcher import fetch_github_search
from app.services.fetchers.github_trending_fetcher import fetch_github_trending
from app.services.fetchers.huggingface_fetcher import fetch_huggingface
from app.services.fetchers.rss_fetcher import fetch_rss

logger = logging.getLogger(__name__)

FETCHER_MAP = {
    "rss": fetch_rss,
    "arxiv": fetch_arxiv,
    "github_trending": fetch_github_trending,
    "github_search": fetch_github_search,
    "huggingface": fetch_huggingface,
    "custom": fetch_rss,
}


def crawl_all(db: Session) -> dict:
    """Run all enabled sources and score new items."""
    sources = db.query(Source).filter(Source.enabled == True).all()  # noqa: E712

    results = {}
    total_new = 0

    for source in sources:
        fetcher = FETCHER_MAP.get(source.type)
        if not fetcher:
            logger.warning("No fetcher for source type: %s", source.type)
            continue
        try:
            count = fetcher(db, source)
            results[source.name] = count
            total_new += count
        except Exception as e:
            logger.error("Error crawling source %s: %s", source.name, e)
            results[source.name] = 0

    scored = scoring_service.score_all_unscored(db)
    logger.info("Crawl complete: %d new items, %d scored", total_new, scored)

    return {"sources": results, "total_new": total_new, "scored": scored}


def crawl_source(db: Session, source_id: int) -> dict:
    """Crawl a single source by ID."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        return {"error": "Source not found"}

    fetcher = FETCHER_MAP.get(source.type)
    if not fetcher:
        return {"error": f"No fetcher for type: {source.type}"}

    count = fetcher(db, source)
    scored = scoring_service.score_all_unscored(db)

    return {"source": source.name, "new_items": count, "scored": scored}
