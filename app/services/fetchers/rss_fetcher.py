import logging
from datetime import datetime, timezone
from typing import Optional
import feedparser
from sqlalchemy.orm import Session
from app.models import Item, Source

logger = logging.getLogger(__name__)


def _parse_date(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _clean_html(text: str) -> str:
    """Strip HTML tags for summary storage."""
    from bs4 import BeautifulSoup
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()[:2000]


def fetch_rss(db: Session, source: Source) -> int:
    """Parse RSS/Atom feed and upsert items. Returns count of new items."""
    try:
        feed = feedparser.parse(source.url)
    except Exception as e:
        logger.error("Failed to parse RSS %s: %s", source.url, e)
        return 0

    if feed.bozo and not feed.entries:
        logger.warning("RSS parse error for %s: %s", source.url, feed.bozo_exception)
        return 0

    count = 0
    for entry in feed.entries:
        link = getattr(entry, "link", None)
        title = getattr(entry, "title", None)
        if not link or not title:
            continue

        exists = db.query(Item).filter(Item.url == link).first()
        if exists:
            continue

        summary = ""
        for attr in ("summary", "description", "content"):
            raw = getattr(entry, attr, None)
            if raw:
                if isinstance(raw, list):
                    raw = raw[0].get("value", "") if raw else ""
                summary = _clean_html(str(raw))
                break

        author = getattr(entry, "author", None)
        published_at = _parse_date(entry)

        item_type = "article"
        if source.type == "arxiv":
            item_type = "paper"

        item = Item(
            source_id=source.id,
            title=title.strip()[:500],
            url=link,
            external_id=getattr(entry, "id", link),
            item_type=item_type,
            author=author,
            published_at=published_at,
            summary_raw=summary,
        )
        db.add(item)
        count += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("DB error saving RSS items from %s: %s", source.url, e)
        return 0

    logger.info("RSS %s: %d new items", source.name, count)
    return count
