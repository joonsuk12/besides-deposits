"""Controller. Spring의 @RestController에 해당한다.

- GET /news/stock/005930?days=90   한 종목의 최근 뉴스 (키포인트 포함, 최신순)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.news import service
from app.news.schemas import NewsResponse

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/stock/{code}", response_model=list[NewsResponse])
def get_by_stock(
    code: str,
    days: int = Query(default=90, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=300),
    db: Session = Depends(get_db),
):
    return service.get_by_stock(db, code, days, limit)
