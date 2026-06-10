from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Keyword
from app.schemas import KeywordOut, KeywordCreate, KeywordUpdate

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=list[KeywordOut])
def list_keywords(db: Session = Depends(get_db)):
    return [KeywordOut.model_validate(k) for k in db.query(Keyword).order_by(Keyword.weight.desc()).all()]


@router.post("", response_model=KeywordOut, status_code=201)
def create_keyword(payload: KeywordCreate, db: Session = Depends(get_db)):
    exists = db.query(Keyword).filter(Keyword.keyword == payload.keyword).first()
    if exists:
        raise HTTPException(status_code=409, detail="Keyword already exists")
    kw = Keyword(**payload.model_dump())
    db.add(kw)
    db.commit()
    db.refresh(kw)
    return KeywordOut.model_validate(kw)


@router.put("/{keyword_id}", response_model=KeywordOut)
def update_keyword(keyword_id: int, payload: KeywordUpdate, db: Session = Depends(get_db)):
    kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(kw, field, value)
    db.commit()
    db.refresh(kw)
    return KeywordOut.model_validate(kw)


@router.delete("/{keyword_id}", status_code=204)
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    db.delete(kw)
    db.commit()
