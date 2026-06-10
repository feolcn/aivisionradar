import logging
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models import Item, Source
from app.config import settings

logger = logging.getLogger(__name__)

TRENDING_BASE = "https://github.com/trending"


def _parse_stars(text: str) -> int:
    text = text.strip().replace(",", "").replace(" stars today", "").replace("stars", "").strip()
    try:
        if "k" in text.lower():
            return int(float(text.lower().replace("k", "")) * 1000)
        return int(text)
    except (ValueError, AttributeError):
        return 0


def fetch_github_trending(db: Session, source: Source) -> int:
    """Scrape GitHub Trending page for repos."""
    headers = {"User-Agent": "Mozilla/5.0 AIVisionRadar/1.0 (https://github.com/aivisionradar)"}
    try:
        resp = httpx.get(
            TRENDING_BASE,
            params={"since": "daily"},
            headers=headers,
            timeout=settings.HTTP_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.error("GitHub Trending fetch failed: %s", e)
        return 0

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article.Box-row")
    count = 0

    for article in articles:
        h2 = article.select_one("h2 a")
        if not h2:
            continue

        repo_path = h2.get("href", "").strip("/")
        if not repo_path or "/" not in repo_path:
            continue

        repo_url = f"https://github.com/{repo_path}"
        exists = db.query(Item).filter(Item.url == repo_url).first()
        if exists:
            continue

        repo_name = repo_path.replace("/", " / ")

        desc_el = article.select_one("p")
        description = desc_el.get_text(strip=True) if desc_el else ""

        stars = 0
        for star_el in article.select("a.Link--muted"):
            txt = star_el.get_text(strip=True)
            if any(c.isdigit() for c in txt):
                stars = _parse_stars(txt)
                break

        item = Item(
            source_id=source.id,
            title=repo_name,
            url=repo_url,
            external_id=repo_path,
            item_type="github_repo",
            summary_raw=description[:500] if description else None,
            stars=stars,
        )
        db.add(item)
        count += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("DB error saving GitHub Trending items: %s", e)
        return 0

    logger.info("GitHub Trending: %d new items", count)
    return count
