from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Source
from app.schemas import SourceOut, SourceCreate, SourceUpdate

router = APIRouter(prefix="/api/sources", tags=["sources"])

VALID_TYPES = {"rss", "arxiv", "github_trending", "github_search", "huggingface", "custom"}


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return [SourceOut.model_validate(s) for s in db.query(Source).order_by(Source.id).all()]


@router.post("", response_model=SourceOut, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    if payload.type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid type: {payload.type}")
    source = Source(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return SourceOut.model_validate(source)


@router.put("/{source_id}", response_model=SourceOut)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return SourceOut.model_validate(source)


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
