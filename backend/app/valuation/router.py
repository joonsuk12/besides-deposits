"""Controller. Spring의 @RestController에 해당한다."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.valuation import service
from app.valuation.schemas import ValuationResponse

router = APIRouter(prefix="/valuation", tags=["valuation"])  # @RequestMapping("/valuation")


@router.get("/stock/{code}", response_model=ValuationResponse)  # @GetMapping("/stock/{code}")
def get_by_stock(code: str, db: Session = Depends(get_db)):
    return service.get_by_stock(db, code)
