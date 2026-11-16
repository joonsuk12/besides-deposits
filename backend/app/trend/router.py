"""Controller. Spring의 @RestController에 해당한다."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.trend import service
from app.trend.schemas import TrendResponse

router = APIRouter(prefix="/trend", tags=["trend"])  # @RequestMapping("/trend")


@router.get("/stock/{code}", response_model=TrendResponse)  # @GetMapping("/stock/{code}")
def get_by_stock(code: str, days: int = Query(default=180, ge=1, le=3650), db: Session = Depends(get_db)):
    """투자자별(외국인·기관·개인) 순매수. days: 최근 며칠치."""
    return service.get_by_stock(db, code, days)
