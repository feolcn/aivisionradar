from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Item


def _today_range():
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def get_daily_report(db: Session, date: datetime | None = None) -> dict:
    """Build daily report data."""
    if date:
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start, _ = _today_range()
    end = start + timedelta(days=1)

    base_q = (
        db.query(Item)
        .filter(Item.created_at >= start)
        .filter(Item.created_at < end)
        .filter(Item.status != "ignored")
    )

    total = base_q.count()

    def top(order_col, limit=20):
        return base_q.order_by(order_col.desc()).limit(limit).all()

    top_items = top(Item.total_score)
    top_reproduce = top(Item.reproduce_score)
    top_content = top(Item.content_score)

    # filter for industrial keywords
    industrial_kws = ["defect", "anomaly", "inspection", "industrial", "工业", "缺陷", "瑕疵"]
    top_industrial = (
        base_q.filter(
            Item.matched_keywords.isnot(None),
        )
        .order_by(Item.total_score.desc())
        .all()
    )
    top_industrial = [
        i for i in top_industrial
        if any(k in (i.matched_keywords or "").lower() for k in industrial_kws)
    ][:10]

    jetson_kws = ["jetson", "tensorrt", "onnx", "orin", "thor"]
    top_jetson = [
        i for i in top(Item.total_score, 50)
        if any(k in (i.matched_keywords or "").lower() for k in jetson_kws)
    ][:10]

    llm_kws = ["vlm", "llm", "agent", "qwen", "vision language", "智能体", "本地大模型"]
    top_llm_agent = [
        i for i in top(Item.total_score, 50)
        if any(k in (i.matched_keywords or "").lower() for k in llm_kws)
    ][:10]

    return {
        "date": start.strftime("%Y-%m-%d"),
        "total_items": total,
        "top_items": top_items[:20],
        "top_reproduce": top_reproduce[:10],
        "top_content": top_content[:10],
        "top_industrial": top_industrial,
        "top_jetson": top_jetson,
        "top_llm_agent": top_llm_agent,
    }


def render_markdown_report(report: dict) -> str:
    """Render report as Markdown string."""
    lines = [
        f"# AIVisionRadar 日报 {report['date']}",
        "",
        f"今日共抓取 {report['total_items']} 条内容",
        "",
    ]

    def section(title: str, items: list, emoji: str = "🔥"):
        lines.append(f"## {emoji} {title}")
        lines.append("")
        if not items:
            lines.append("_暂无内容_")
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. **[{item.title}]({item.url})**")
            lines.append(f"   - 总分: {item.total_score:.1f} | 命中关键词: {item.matched_keywords or '无'}")
            if item.ai_summary:
                lines.append(f"   - {item.ai_summary[:150]}")
            lines.append("")

    section("综合 Top 20", report["top_items"], "🔥")
    section("最值得复现", report["top_reproduce"], "🛠️")
    section("最值得写文章", report["top_content"], "✍️")
    section("最适合工业检测", report["top_industrial"], "🏭")
    section("最适合 Jetson/TensorRT", report["top_jetson"], "⚡")
    section("最适合本地大模型/Agent", report["top_llm_agent"], "🤖")

    lines.append("---")
    lines.append(f"_由 AIVisionRadar 自动生成 · {report['date']}_")
    return "\n".join(lines)
