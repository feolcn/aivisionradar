from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Item, Keyword, Setting, Source
from app.services.report_service import get_daily_report, render_markdown_report
from app.services.summary_service import is_translation_enabled

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


def _tmpl(request: Request, name: str, ctx: dict):
    """Wrapper that uses the new Starlette 1.x TemplateResponse signature."""
    return templates.TemplateResponse(request, name, ctx)


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    today_count = db.query(Item).filter(
        Item.created_at >= today_start,
        Item.created_at < today_end,
    ).count()

    high_score_count = db.query(Item).filter(
        Item.created_at >= today_start,
        Item.created_at < today_end,
        Item.total_score >= 5.0,
    ).count()

    top_items = (
        db.query(Item)
        .filter(Item.status != "ignored")
        .order_by(Item.total_score.desc())
        .limit(20)
        .all()
    )

    kw_stats: dict[str, int] = {}
    for item in db.query(Item).filter(Item.matched_keywords != None, Item.matched_keywords != "").all():  # noqa: E711
        for kw in (item.matched_keywords or "").split(","):
            kw = kw.strip()
            if kw:
                kw_stats[kw] = kw_stats.get(kw, 0) + 1
    kw_stats_sorted = sorted(kw_stats.items(), key=lambda x: x[1], reverse=True)[:20]

    source_stats = (
        db.query(Source.name, func.count(Item.id).label("count"))
        .join(Item, Item.source_id == Source.id, isouter=True)
        .group_by(Source.name)
        .order_by(func.count(Item.id).desc())
        .all()
    )

    return _tmpl(request, "dashboard.html", {
        "today_count": today_count,
        "high_score_count": high_score_count,
        "top_items": top_items,
        "kw_stats": kw_stats_sorted,
        "source_stats": source_stats,
    })


@router.get("/items")
def items_list(
    request: Request,
    page: int = 1,
    item_type: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    page_size = 20
    query = db.query(Item)

    if item_type:
        query = query.filter(Item.item_type == item_type)
    if status:
        query = query.filter(Item.status == status)
    if q:
        query = query.filter(Item.title.ilike(f"%{q}%"))

    total = query.count()
    items = (
        query.order_by(Item.total_score.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    pages = (total + page_size - 1) // page_size

    return _tmpl(request, "items.html", {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "page_size": page_size,
        "item_type": item_type or "",
        "status": status or "",
        "q": q or "",
    })


@router.get("/items/{item_id}")
def item_detail(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    source = db.query(Source).filter(Source.id == item.source_id).first() if item.source_id else None
    return _tmpl(request, "item_detail.html", {"item": item, "source": source})


@router.post("/items/{item_id}/status")
def update_item_status_web(item_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if status in {"new", "saved", "ignored", "done"}:
        item.status = status
        db.commit()
    return RedirectResponse(url=f"/items/{item_id}", status_code=303)


@router.get("/sources")
def sources_list(request: Request, db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.id).all()
    return _tmpl(request, "sources.html", {"sources": sources})


@router.post("/sources")
def create_source_web(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    url: str = Form(...),
    category: str = Form(""),
    db: Session = Depends(get_db),
):
    source = Source(name=name, type=type, url=url, category=category or None)
    db.add(source)
    db.commit()
    return RedirectResponse(url="/sources", status_code=303)


@router.post("/sources/{source_id}/toggle")
def toggle_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if source:
        source.enabled = not source.enabled
        db.commit()
    return RedirectResponse(url="/sources", status_code=303)


@router.post("/sources/{source_id}/delete")
def delete_source_web(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if source:
        db.delete(source)
        db.commit()
    return RedirectResponse(url="/sources", status_code=303)


@router.get("/keywords")
def keywords_list(request: Request, db: Session = Depends(get_db)):
    keywords = db.query(Keyword).order_by(Keyword.weight.desc()).all()
    return _tmpl(request, "keywords.html", {"keywords": keywords})


@router.post("/keywords")
def create_keyword_web(
    keyword: str = Form(...),
    category: str = Form(""),
    weight: float = Form(1.0),
    db: Session = Depends(get_db),
):
    exists = db.query(Keyword).filter(Keyword.keyword == keyword).first()
    if not exists:
        db.add(Keyword(keyword=keyword, category=category or None, weight=weight))
        db.commit()
    return RedirectResponse(url="/keywords", status_code=303)


@router.post("/keywords/{keyword_id}/toggle")
def toggle_keyword(keyword_id: int, db: Session = Depends(get_db)):
    kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if kw:
        kw.enabled = not kw.enabled
        db.commit()
    return RedirectResponse(url="/keywords", status_code=303)


@router.post("/keywords/{keyword_id}/delete")
def delete_keyword_web(keyword_id: int, db: Session = Depends(get_db)):
    kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if kw:
        db.delete(kw)
        db.commit()
    return RedirectResponse(url="/keywords", status_code=303)


@router.get("/reports/daily")
def daily_report_page(request: Request, db: Session = Depends(get_db)):
    report = get_daily_report(db)
    return _tmpl(request, "daily_report.html", {"report": report})


@router.get("/reports/daily.md", response_class=PlainTextResponse)
def daily_report_md_download(db: Session = Depends(get_db)):
    report = get_daily_report(db)
    md = render_markdown_report(report)
    return PlainTextResponse(content=md, media_type="text/markdown")


@router.get("/settings")
def settings_page(request: Request, db: Session = Depends(get_db)):
    all_settings = db.query(Setting).order_by(Setting.id).all()
    has_ai_key = bool(settings.AI_API_KEY)
    translation_on = is_translation_enabled(db)
    return _tmpl(request, "settings.html", {
        "all_settings": all_settings,
        "has_ai_key": has_ai_key,
        "translation_on": translation_on,
        "ai_model": settings.AI_MODEL,
    })


@router.post("/settings/{key}")
def update_setting(key: str, value: str = Form(...), db: Session = Depends(get_db)):
    row = db.query(Setting).filter(Setting.key == key).first()
    if row:
        row.value = value
        db.commit()
    return RedirectResponse(url="/settings", status_code=303)
