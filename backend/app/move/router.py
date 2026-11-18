"""Controller. Spring의 @RestController에 해당한다.

- GET /moves/005930?days=365   크게 움직인 날 목록 + 같은 날 시장 지수·공시·투자자별 매매
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.move import service
from app.move.schemas import MovesResponse

router = APIRouter(prefix="/moves", tags=["move"])


@router.get("/{code}", response_model=MovesResponse)
def get_moves(code: str, days: int = Query(default=365, ge=30, le=3650), db: Session = Depends(get_db)):
    return service.get_moves(db, code, days)
