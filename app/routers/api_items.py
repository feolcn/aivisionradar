from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Item
from app.schemas import ItemOut, ItemStatusUpdate, PaginatedItems

router = APIRouter(prefix="/api/items", tags=["items"])

VALID_STATUSES = {"new", "saved", "ignored", "done"}
VALID_TYPES = {"article", "paper", "github_repo", "model", "video", "unknown"}


@router.get("", response_model=PaginatedItems)
def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    item_type: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Item)
    if item_type and item_type in VALID_TYPES:
        query = query.filter(Item.item_type == item_type)
    if status and status in VALID_STATUSES:
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

    return PaginatedItems(
        items=[ItemOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemOut.model_validate(item)


@router.post("/{item_id}/status", response_model=ItemOut)
def update_item_status(
    item_id: int,
    payload: ItemStatusUpdate,
    db: Session = Depends(get_db),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return ItemOut.model_validate(item)
