from typing import Optional
from sqlalchemy.orm import Session
from app.models import Item, Keyword

INDUSTRIAL_KEYWORDS = {"defect", "anomaly", "inspection", "industrial", "fabric", "textile", "工业", "缺陷", "瑕疵", "检测"}
EDGE_AI_KEYWORDS = {"jetson", "tensorrt", "onnx", "orin", "thor", "edge"}
LLM_AGENT_KEYWORDS = {"llm", "agent", "vlm", "vision language", "local llm", "qwen", "智能体", "本地大模型", "视觉语言"}
REPRODUCE_KEYWORDS = {"code", "demo", "pretrained", "checkpoint", "model", "weights", "implementation"}
CONTENT_KEYWORDS = {"benchmark", "comparison", "tutorial", "guide", "deploy", "how to", "howto", "survey"}


def _text_lower(item: Item) -> str:
    parts = [item.title or "", item.summary_raw or ""]
    return " ".join(parts).lower()


def compute_relevance_score(item: Item, keywords: list[Keyword]) -> tuple[float, list[str]]:
    """Compute relevance score based on keyword matching."""
    text = _text_lower(item)
    title_lower = (item.title or "").lower()
    score = 0.0
    matched: list[str] = []

    for kw in keywords:
        if not kw.enabled:
            continue
        kw_lower = kw.keyword.lower()
        if kw_lower in text:
            hit_score = kw.weight
            if kw_lower in title_lower:
                hit_score *= 2
            # bonus for category
            if any(ind in kw_lower for ind in INDUSTRIAL_KEYWORDS):
                hit_score += 3
            elif any(edge in kw_lower for edge in EDGE_AI_KEYWORDS):
                hit_score += 2
            elif any(llm in kw_lower for llm in LLM_AGENT_KEYWORDS):
                hit_score += 2
            score += hit_score
            matched.append(kw.keyword)

    return score, matched


def compute_reproduce_score(item: Item) -> float:
    """Estimate how easy/valuable this item is to reproduce."""
    text = _text_lower(item)
    score = 0.0

    if item.item_type == "github_repo":
        score += 3

    if any(k in text for k in REPRODUCE_KEYWORDS):
        score += 2

    if any(k in text for k in {"tensorrt", "onnx", "jetson", "docker"}):
        score += 2

    if any(k in text for k in {"defect", "anomaly", "industrial", "segmentation"}):
        score += 2

    # star bonus
    if item.stars is not None:
        if item.stars >= 10000:
            score += 5
        elif item.stars >= 1000:
            score += 4
        elif item.stars >= 100:
            score += 2

    return score


def compute_content_score(item: Item) -> float:
    """Estimate content/article value."""
    text = _text_lower(item)
    score = 0.0

    if any(k in text for k in CONTENT_KEYWORDS):
        score += 2

    if item.stars is not None:
        if item.stars >= 10000:
            score += 5
        elif item.stars >= 1000:
            score += 4
        elif item.stars >= 100:
            score += 2

    return score


def compute_monetization_score(item: Item) -> float:
    """Estimate commercial/monetization potential."""
    text = _text_lower(item)
    score = 0.0

    if any(k in text for k in {"industrial", "inspection", "defect", "automation", "enterprise", "deploy"}):
        score += 3

    if any(k in text for k in {"local", "self-hosted", "private deployment", "on-premise", "边缘", "本地"}):
        score += 2

    return score


def compute_total_score(r: float, rep: float, c: float, m: float) -> float:
    return r * 0.45 + rep * 0.25 + c * 0.2 + m * 0.1


def score_item(item: Item, keywords: list[Keyword]) -> Item:
    """Score a single item in place."""
    relevance, matched = compute_relevance_score(item, keywords)
    reproduce = compute_reproduce_score(item)
    content = compute_content_score(item)
    monetization = compute_monetization_score(item)
    total = compute_total_score(relevance, reproduce, content, monetization)

    item.relevance_score = round(relevance, 2)
    item.reproduce_score = round(reproduce, 2)
    item.content_score = round(content, 2)
    item.monetization_score = round(monetization, 2)
    item.total_score = round(total, 2)
    item.matched_keywords = ", ".join(matched) if matched else ""

    return item


def score_all_unscored(db: Session) -> int:
    """Score all items that have total_score == 0."""
    keywords = db.query(Keyword).filter(Keyword.enabled == True).all()  # noqa: E712
    items = db.query(Item).filter(Item.total_score == 0.0).all()

    for item in items:
        score_item(item, keywords)

    db.commit()
    return len(items)


def rescore_all(db: Session) -> int:
    """Re-score all items."""
    keywords = db.query(Keyword).filter(Keyword.enabled == True).all()  # noqa: E712
    items = db.query(Item).all()

    for item in items:
        score_item(item, keywords)

    db.commit()
    return len(items)
