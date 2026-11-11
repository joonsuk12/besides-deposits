"""Controller. Spring의 @RestController에 해당한다.

- APIRouter(prefix="/stocks")   = @RequestMapping("/stocks")
- @router.get("/{code}/prices") = @GetMapping("/{code}/prices")
- code: str                     = @PathVariable
- days: int = 365               = @RequestParam(defaultValue = "365")
- db: Session = Depends(get_db) = 의존성 주입 (@Autowired)
- response_model                = 응답 DTO 타입

주의: "/watchlist"처럼 고정된 경로는 "/{code}"보다 위에 적어야 한다 (위에서부터 먼저 맞는 경로가 선택된다).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.stock import service
from app.stock.schemas import CollectResult, PriceResponse, StockResponse, WatchlistItem

router = APIRouter(prefix="/stocks", tags=["stock"])


@router.get("", response_model=list[StockResponse])
def get_stocks(db: Session = Depends(get_db)):
    """전체 종목 목록 (검색창 자동완성용)."""
    return service.get_stocks(db)


@router.get("/watchlist", response_model=list[WatchlistItem])
def get_watchlist(db: Session = Depends(get_db)):
    """관심 종목 목록과 최근 종가."""
    return service.get_watchlist(db)


@router.post("/collect", response_model=list[CollectResult])
def collect(db: Session = Depends(get_db)):
    """관심 종목의 주가를 지금 수집한다."""
    return service.collect_watchlist_prices(db)


@router.get("/{code}", response_model=StockResponse)
def get_stock(code: str, db: Session = Depends(get_db)):
    """종목 하나의 정보."""
    return service.get_stock(db, code)


@router.get("/{code}/prices", response_model=list[PriceResponse])
def get_prices(code: str, days: int = Query(default=365, ge=1, le=3650), db: Session = Depends(get_db)):
    """종목의 최근 days일 일봉."""
    return service.get_prices(db, code, days)


@router.put("/{code}/watch", response_model=StockResponse)
def add_watch(code: str, db: Session = Depends(get_db)):
    """관심 종목에 추가."""
    return service.set_watched(db, code, True)


@router.delete("/{code}/watch", response_model=StockResponse)
def remove_watch(code: str, db: Session = Depends(get_db)):
    """관심 종목에서 제거."""
    return service.set_watched(db, code, False)
