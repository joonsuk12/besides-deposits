"""Controller. Spring의 @RestController에 해당한다.

- GET /disclosures/stock/005930?days=180   한 종목의 공시 (초보용 분류·설명 포함, 최신순)
- POST /disclosures/collect                관심 종목 공시를 지금 새로 받기
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.disclosure import service
from app.disclosure.schemas import DisclosureListResponse

router = APIRouter(prefix="/disclosures", tags=["disclosure"])


@router.get("/stock/{code}", response_model=DisclosureListResponse)
def get_by_stock(code: str, days: int = Query(default=180, ge=1, le=730), db: Session = Depends(get_db)):
    return service.get_by_stock(db, code, days)


@router.post("/collect")
def collect(db: Session = Depends(get_db)):
    return {"saved": service.collect_watchlist(db)}
