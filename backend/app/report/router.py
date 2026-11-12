"""Controller. Spring의 @RestController에 해당한다.

- GET /reports?date=2026-11-12   그날 나온 종목 리포트 전체 (기본: 오늘)
- GET /reports/stock/005930      한 종목의 최근 리포트
- POST /reports/collect?days=7   최근 며칠치를 지금 받아 두기
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.report import service
from app.report.schemas import ReportFeedResponse, ReportResponse

router = APIRouter(prefix="/reports", tags=["report"])


@router.get("", response_model=ReportFeedResponse)
def get_feed(day: date | None = Query(default=None, alias="date"), db: Session = Depends(get_db)):
    return service.get_feed(db, day or date.today())


@router.get("/stock/{code}", response_model=list[ReportResponse])
def get_by_stock(code: str, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    return service.get_by_stock(db, code, limit)


@router.post("/collect")
def collect(days: int = Query(default=7, ge=1, le=30), db: Session = Depends(get_db)):
    return {"saved": service.collect_recent_days(db, days)}
