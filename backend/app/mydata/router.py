"""Controller. Spring의 @RestController에 해당한다.

- POST /mydata                               답 하나 저장
- GET  /mydata?kind=risk_reaction&stock_code=005930&limit=5   기록 조회 (최신순)
- GET  /mydata/export                        전체 기록을 JSON으로 (나중에 가공·백업용)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.mydata import service
from app.mydata.schemas import MyRecordCreate, MyRecordResponse

router = APIRouter(prefix="/mydata", tags=["mydata"])


@router.post("", response_model=MyRecordResponse)
def create(req: MyRecordCreate, db: Session = Depends(get_db)):
    return service.create(db, req)


@router.get("", response_model=list[MyRecordResponse])
def find(
    kind: str | None = None,
    stock_code: str | None = None,
    limit: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return service.find(db, kind, stock_code, limit)


@router.get("/export", response_model=list[MyRecordResponse])
def export(db: Session = Depends(get_db)):
    return service.find(db, None, None, None)
