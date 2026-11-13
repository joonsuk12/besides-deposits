"""Controller. Spring의 @RestController에 해당한다.

- GET /reports?date=2026-11-12   그날 나온 종목 리포트 전체 (기본: 오늘)
- GET /reports/stock/005930      한 종목의 최근 리포트
- POST /reports/collect?days=7   최근 며칠치를 지금 받아 두기
- GET /reports/easy/pending      쉬운 요약이 아직 없는 리포트 (요약 쓰는 쪽이 가져가는 재료)
- POST /reports/easy             Claude가 쓴 쉬운 요약 저장 (여러 건을 한 번에)

※ "/easy/pending"처럼 고정된 경로를 위에 둔다 (Spring과 달리 위에서부터 먼저 맞는 경로가 선택된다).
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.report import service
from app.report.schemas import EasyPending, EasySaveRequest, ReportFeedResponse, ReportResponse

router = APIRouter(prefix="/reports", tags=["report"])


@router.get("", response_model=ReportFeedResponse)
def get_feed(day: date | None = Query(default=None, alias="date"), db: Session = Depends(get_db)):
    return service.get_feed(db, day or date.today())


@router.get("/easy/pending", response_model=list[EasyPending])
def get_easy_pending(
    days: int = Query(default=3, ge=1, le=60),
    limit: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return service.get_easy_pending(db, days, limit)


@router.post("/easy")
def save_easy(items: list[EasySaveRequest], db: Session = Depends(get_db)):
    """@RequestBody List<EasySaveRequest>와 같다. 본문 JSON을 Pydantic이 검증한다."""
    return {"saved": service.save_easy(db, items)}


@router.get("/stock/{code}", response_model=list[ReportResponse])
def get_by_stock(code: str, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    return service.get_by_stock(db, code, limit)


@router.post("/collect")
def collect(days: int = Query(default=7, ge=1, le=30), db: Session = Depends(get_db)):
    return {"saved": service.collect_recent_days(db, days)}
