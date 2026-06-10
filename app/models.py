from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    items: Mapped[list["Item"]] = relationship("Item", back_populates="source")


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sources.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(500))
    item_type: Mapped[str] = mapped_column(String(50), default="unknown")
    author: Mapped[Optional[str]] = mapped_column(String(500))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    summary_raw: Mapped[Optional[str]] = mapped_column(Text)
    # Chinese translation fields
    title_zh: Mapped[Optional[str]] = mapped_column(String(500))
    summary_zh: Mapped[Optional[str]] = mapped_column(Text)
    # AI analysis fields
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    why_relevant: Mapped[Optional[str]] = mapped_column(Text)
    reproduce_suggestion: Mapped[Optional[str]] = mapped_column(Text)
    content_ideas: Mapped[Optional[str]] = mapped_column(Text)
    matched_keywords: Mapped[Optional[str]] = mapped_column(Text)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    reproduce_score: Mapped[float] = mapped_column(Float, default=0.0)
    content_score: Mapped[float] = mapped_column(Float, default=0.0)
    monetization_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    stars: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="items")


class Setting(Base):
    """Key-value store for UI-configurable settings."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    value_type: Mapped[str] = mapped_column(String(20), default="bool")  # bool / str / int
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
