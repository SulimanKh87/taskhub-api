from pydantic import BaseModel, Field
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class PageMeta(BaseModel):
    limit: int = Field(..., ge=1, le=100)
    next_cursor: Optional[str] = None
    has_more: bool


class Page(BaseModel, Generic[T]):
    items: List[T]
    meta: PageMeta
