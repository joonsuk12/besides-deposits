"""Controller. Spring의 @RestController에 해당한다.

- APIRouter(prefix="/stocks")   = @RequestMapping("/stocks")
- @router.get("/{code}/prices") = @GetMapping("/{code}/prices")
- code: str                     = @PathVariable
- days: int = 365               = @RequestParam(defaultValue = "365")
- db: Session = Depends(get_db) = 의존성 주입 (@Autowired)
- response_model                = 응답 DTO 타입
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.stock import service
from app.stock.schemas import CollectResult, PriceResponse, StockResponse

router = APIRouter(prefix="/stocks", tags=["stock"])


@router.get("", response_model=list[StockResponse])
def get_stocks(db: Session = Depends(get_db)):
    """종목 목록."""
    return service.get_stocks(db)


@router.get("/{code}/prices", response_model=list[PriceResponse])
def get_prices(code: str, days: int = Query(default=365, ge=1, le=3650), db: Session = Depends(get_db)):
    """종목의 최근 days일 일봉."""
    return service.get_prices(db, code, days)


@router.post("/collect", response_model=list[CollectResult])
def collect(db: Session = Depends(get_db)):
    """관심 종목의 주가를 지금 수집한다."""
    return service.collect_watchlist_prices(db)
