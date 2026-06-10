import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Item
from app.config import settings

logger = logging.getLogger(__name__)

FALLBACK_TEMPLATE = """【AI摘要未启用】
标题：{title}
来源链接：{url}
关键词命中：{keywords}

请配置 AI_API_KEY 和 AI_BASE_URL 以启用 AI 摘要功能。"""

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


def _make_fallback(item: Item) -> dict:
    return {
        "ai_summary": FALLBACK_TEMPLATE.format(
            title=item.title,
            url=item.url,
            keywords=item.matched_keywords or "无",
        ),
        "why_relevant": "请配置 AI_API_KEY 以获取智能分析。",
        "reproduce_suggestion": "请配置 AI_API_KEY 以获取复现建议。",
        "content_ideas": "请配置 AI_API_KEY 以获取创作思路。",
    }


async def _call_ai(title: str, url: str, summary: str, keywords: str) -> Optional[dict]:
    """Call OpenAI-compatible API for summary."""
    import httpx
    import json

    prompt = SUMMARY_PROMPT.format(
        title=title,
        url=url,
        summary=summary[:1000] if summary else "无摘要",
        keywords=keywords or "无",
    )

    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 800,
    }

    base_url = settings.AI_BASE_URL.rstrip("/")
    url_endpoint = f"{base_url}/chat/completions"

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url_endpoint, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        return json.loads(content)


async def summarize_item(item: Item) -> dict:
    """Generate AI summary for an item, falling back gracefully if AI unavailable."""
    if not settings.AI_API_KEY:
        return _make_fallback(item)

    try:
        result = await _call_ai(
            title=item.title,
            url=item.url,
            summary=item.summary_raw or "",
            keywords=item.matched_keywords or "",
        )
        if result:
            return result
    except Exception as e:
        logger.warning("AI summary failed for item %s: %s", item.id, e)

    return _make_fallback(item)


async def summarize_pending(db: Session, limit: int = 20) -> int:
    """Summarize items that have no ai_summary yet."""
    items = (
        db.query(Item)
        .filter(Item.ai_summary == None)  # noqa: E711
        .filter(Item.total_score > 0)
        .order_by(Item.total_score.desc())
        .limit(limit)
        .all()
    )

    count = 0
    for item in items:
        result = await summarize_item(item)
        item.ai_summary = result.get("ai_summary", "")
        item.why_relevant = result.get("why_relevant", "")
        item.reproduce_suggestion = result.get("reproduce_suggestion", "")
        item.content_ideas = result.get("content_ideas", "")
        count += 1

    db.commit()
    return count
