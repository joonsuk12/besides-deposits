"""Controller. Spring의 @RestController에 해당한다."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.valuation import service
from app.valuation.schemas import OverviewResponse, ValuationResponse

router = APIRouter(prefix="/valuation", tags=["valuation"])  # @RequestMapping("/valuation")


@router.get("/stock/{code}", response_model=ValuationResponse)  # @GetMapping("/stock/{code}")
def get_by_stock(code: str, db: Session = Depends(get_db)):
    return service.get_by_stock(db, code)


@router.get("/stock/{code}/overview", response_model=OverviewResponse)  # @GetMapping("/stock/{code}/overview")
def get_overview(code: str, db: Session = Depends(get_db)):
    return service.get_overview(db, code)
