import logging
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Item, Source

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com/search/repositories"


def fetch_github_search(db: Session, source: Source) -> int:
    """Search GitHub repositories using the Search API."""
    if not settings.GITHUB_TOKEN:
        logger.info("GITHUB_TOKEN not set, skipping GitHub Search for: %s", source.url)
        return 0

    query = source.url  # source.url stores the search query string
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    params = {
        "q": query,
        "sort": "updated",
        "order": "desc",
        "per_page": 30,
    }

    try:
        resp = httpx.get(
            GITHUB_API,
            headers=headers,
            params=params,
            timeout=settings.HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.error("GitHub Search API failed for '%s': %s", query, e)
        return 0

    data = resp.json()
    repos = data.get("items", [])
    count = 0

    for repo in repos:
        repo_url = repo.get("html_url", "")
        if not repo_url:
            continue

        exists = db.query(Item).filter(Item.url == repo_url).first()
        if exists:
            continue

        pushed_at_str = repo.get("pushed_at") or repo.get("updated_at")
        published_at = None
        if pushed_at_str:
            try:
                published_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        item = Item(
            source_id=source.id,
            title=repo.get("full_name", repo_url),
            url=repo_url,
            external_id=str(repo.get("id", "")),
            item_type="github_repo",
            author=repo.get("owner", {}).get("login"),
            published_at=published_at,
            summary_raw=(repo.get("description") or "")[:500],
            stars=repo.get("stargazers_count", 0),
        )
        db.add(item)
        count += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("DB error saving GitHub Search items: %s", e)
        return 0

    logger.info("GitHub Search '%s': %d new items", query, count)
    return count
