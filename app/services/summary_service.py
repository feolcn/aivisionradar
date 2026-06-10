import json
import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Item, Setting

logger = logging.getLogger(__name__)

FALLBACK_TEMPLATE = """【AI摘要未启用】请配置 AI_API_KEY 和 AI_BASE_URL 以启用 AI 摘要功能。"""

SUMMARY_PROMPT = """你是一个面向 AI 工程师和工业视觉工程师的技术情报分析师。

请分析以下内容，并用中文输出 JSON 格式分析报告：

标题：{title}
链接：{url}
摘要：{summary}
命中关键词：{keywords}

请输出以下 JSON 字段：
{{
  "ai_summary": "用2-3句话描述这个内容讲什么",
  "why_relevant": "为什么值得关注，从工业视觉/边缘AI/本地大模型角度分析",
  "reproduce_suggestion": "是否适合在 RTX 3090 / Jetson Orin / Thor 上复现，给出建议",
  "content_ideas": "可以写成什么公众号文章/视频号/GitHub项目内容，给出1-3个创作思路"
}}

注意：
1. 只输出 JSON，不要有额外说明
2. 所有字段都必须有内容，不能为 null
3. ai_summary 不超过 200 字
4. why_relevant 不超过 150 字
5. reproduce_suggestion 不超过 100 字
6. content_ideas 不超过 200 字"""

TRANSLATION_PROMPT = """将以下英文标题和摘要翻译成{lang}，输出 JSON：

标题：{title}
摘要：{summary}

输出格式（只输出 JSON，不要额外说明）：
{{"title_zh": "中文标题", "summary_zh": "中文摘要（不超过150字）"}}"""


def _get_setting(db: Session, key: str, default: str = "") -> str:
    """Read a setting value from DB."""
    row = db.query(Setting).filter(Setting.key == key).first()
    return row.value if row else default


def is_translation_enabled(db: Session) -> bool:
    val = _get_setting(db, "enable_translation", "false")
    return val.lower() == "true"


def is_ai_summary_enabled(db: Session) -> bool:
    val = _get_setting(db, "enable_ai_summary", "false")
    return val.lower() == "true"


def _needs_translation(item: Item) -> bool:
    """Return True if the item title looks like it needs translation."""
    title = item.title or ""
    ascii_ratio = sum(1 for c in title if ord(c) < 128) / max(len(title), 1)
    return ascii_ratio > 0.7  # mostly ASCII → likely English


def _make_fallback(item: Item) -> dict:
    return {
        "ai_summary": FALLBACK_TEMPLATE,
        "why_relevant": "请配置 AI_API_KEY 以获取智能分析。",
        "reproduce_suggestion": "请配置 AI_API_KEY 以获取复现建议。",
        "content_ideas": "请配置 AI_API_KEY 以获取创作思路。",
    }


def _is_ollama() -> bool:
    """Detect if AI_BASE_URL points to a local Ollama instance."""
    url = settings.AI_BASE_URL.lower()
    return "11434" in url or settings.AI_API_KEY.lower() == "ollama"


def _extract_json(content: str) -> dict:
    """Extract the first JSON object from a string."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end > start:
        content = content[start:end]
    return json.loads(content)


async def _call_ai_ollama(prompt: str, max_tokens: int = 400) -> Optional[dict]:
    """Call Ollama native API with thinking disabled for fast responses."""
    base = settings.AI_BASE_URL.rstrip("/")
    # Strip /v1 suffix to get Ollama base URL
    if base.endswith("/v1"):
        base = base[:-3]
    payload = {
        "model": settings.AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "think": False,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": max_tokens},
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(f"{base}/api/chat", json=payload)
        resp.raise_for_status()
        content = resp.json()["message"]["content"].strip()
        return _extract_json(content)


async def _call_ai_openai(prompt: str, max_tokens: int = 800) -> Optional[dict]:
    """Call OpenAI-compatible API."""
    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    base_url = settings.AI_BASE_URL.rstrip("/")
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        return _extract_json(content)


async def _call_ai(prompt: str, max_tokens: int = 800) -> Optional[dict]:
    """Call AI API and parse JSON response. Auto-detects Ollama vs OpenAI."""
    if _is_ollama():
        return await _call_ai_ollama(prompt, max_tokens)
    return await _call_ai_openai(prompt, max_tokens)


async def translate_item(item: Item, lang: str = "简体中文") -> Optional[dict]:
    """Translate title and summary to Chinese. Returns {title_zh, summary_zh} or None."""
    if not settings.AI_API_KEY:
        return None
    if not _needs_translation(item):
        return None

    prompt = TRANSLATION_PROMPT.format(
        lang=lang,
        title=item.title,
        summary=(item.summary_raw or "")[:500],
    )
    try:
        result = await _call_ai(prompt, max_tokens=300)
        if result and "title_zh" in result:
            return result
    except Exception as e:
        logger.warning("Translation failed for item %s: %s", item.id, e)
    return None


async def summarize_item(item: Item) -> dict:
    """Generate AI summary for an item, falling back gracefully if AI unavailable."""
    if not settings.AI_API_KEY:
        return _make_fallback(item)

    prompt = SUMMARY_PROMPT.format(
        title=item.title,
        url=item.url,
        summary=(item.summary_raw or "")[:1000] or "无摘要",
        keywords=item.matched_keywords or "无",
    )
    try:
        result = await _call_ai(prompt, max_tokens=800)
        if result:
            return result
    except Exception as e:
        logger.warning("AI summary failed for item %s: %s", item.id, e)

    return _make_fallback(item)


async def summarize_pending(db: Session, limit: int = 20) -> int:
    """Summarize and/or translate pending items based on settings."""
    do_summary = is_ai_summary_enabled(db) and bool(settings.AI_API_KEY)
    do_translate = is_translation_enabled(db) and bool(settings.AI_API_KEY)

    if not do_summary and not do_translate:
        logger.info("Both AI summary and translation are disabled, skipping.")
        return 0

    lang_code = _get_setting(db, "translation_language", "zh-CN")
    lang = "繁体中文" if lang_code == "zh-TW" else "简体中文"

    items = (
        db.query(Item)
        .filter(Item.total_score > 0)
        .filter(
            (Item.ai_summary == None) | (Item.title_zh == None)  # noqa: E711
        )
        .order_by(Item.total_score.desc())
        .limit(limit)
        .all()
    )

    count = 0
    for item in items:
        if do_summary and not item.ai_summary:
            result = await summarize_item(item)
            item.ai_summary = result.get("ai_summary", "")
            item.why_relevant = result.get("why_relevant", "")
            item.reproduce_suggestion = result.get("reproduce_suggestion", "")
            item.content_ideas = result.get("content_ideas", "")

        if do_translate and not item.title_zh:
            trans = await translate_item(item, lang)
            if trans:
                item.title_zh = trans.get("title_zh", "")
                item.summary_zh = trans.get("summary_zh", "")

        count += 1

    db.commit()
    return count


async def translate_pending(db: Session, limit: int = 50) -> int:
    """Translate items that have no title_zh yet."""
    if not settings.AI_API_KEY:
        return 0

    lang_code = _get_setting(db, "translation_language", "zh-CN")
    lang = "繁体中文" if lang_code == "zh-TW" else "简体中文"

    items = (
        db.query(Item)
        .filter(Item.title_zh == None)  # noqa: E711
        .filter(Item.total_score > 0)
        .order_by(Item.total_score.desc())
        .limit(limit)
        .all()
    )

    count = 0
    for item in items:
        trans = await translate_item(item, lang)
        if trans:
            item.title_zh = trans.get("title_zh", "")
            item.summary_zh = trans.get("summary_zh", "")
            count += 1

    db.commit()
    return count
