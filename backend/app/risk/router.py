"""Controller. Spring의 @RestController에 해당한다.

- GET /risk/005930   한 종목의 위험 신호 점검 (신호등 + 근거 공시·숫자)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.risk import service
from app.risk.schemas import RiskResponse

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/{code}", response_model=RiskResponse)
def get_by_stock(code: str, db: Session = Depends(get_db)):
    return service.get_by_stock(db, code)
