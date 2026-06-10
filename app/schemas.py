from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SourceBase(BaseModel):
    name: str
    type: str
    url: str
    category: Optional[str] = None
    enabled: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    enabled: Optional[bool] = None


class SourceOut(SourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class KeywordBase(BaseModel):
    keyword: str
    category: Optional[str] = None
    weight: float = 1.0
    enabled: bool = True


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(BaseModel):
    keyword: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = None
    enabled: Optional[bool] = None


class KeywordOut(KeywordBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class ItemBase(BaseModel):
    title: str
    url: str
    item_type: str = "unknown"
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    summary_raw: Optional[str] = None


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_id: Optional[int] = None
    title_zh: Optional[str] = None
    summary_zh: Optional[str] = None
    ai_summary: Optional[str] = None
    why_relevant: Optional[str] = None
    reproduce_suggestion: Optional[str] = None
    content_ideas: Optional[str] = None
    matched_keywords: Optional[str] = None
    relevance_score: float
    reproduce_score: float
    content_score: float
    monetization_score: float
    total_score: float
    stars: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime


class ItemStatusUpdate(BaseModel):
    status: str


class PaginatedItems(BaseModel):
    items: list[ItemOut]
    total: int
    page: int
    page_size: int
    pages: int


class DailyReportOut(BaseModel):
    date: str
    total_items: int
    top_items: list[ItemOut]
    top_reproduce: list[ItemOut]
    top_content: list[ItemOut]
    top_industrial: list[ItemOut]
    top_jetson: list[ItemOut]
    top_llm_agent: list[ItemOut]
