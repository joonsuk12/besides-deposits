"""Controller. Spring의 @RestController에 해당한다."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.etf import service
from app.etf.schemas import EtfResponse

router = APIRouter(prefix="/etf", tags=["etf"])  # @RequestMapping("/etf")


@router.get("/{code}", response_model=EtfResponse)  # @GetMapping("/{code}")
def get_by_stock(code: str, db: Session = Depends(get_db)):
    """ETF 정보: 따라가는 지수, 보수, 괴리율, 담긴 종목, 수익률, 분배금 등."""
    return service.get_by_stock(db, code)
