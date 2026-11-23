"""Controller. Spring의 @RestController에 해당한다.

- GET  /practice/question?code=005930   타임머신 문제 하나 (code를 빼면 무작위 종목)
- POST /practice/answer                 답을 내면 결과를 계산해 돌려주고 마이데이터에 저장
- GET  /practice/history                지금까지 푼 문제와 맞힌 비율, 이유별 정답률
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.practice import service
from app.practice.schemas import AnswerRequest, AnswerResponse, HistoryResponse, QuestionResponse

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/question", response_model=QuestionResponse)
def get_question(code: str | None = None, db: Session = Depends(get_db)):
    return service.get_question(db, code)


@router.post("/answer", response_model=AnswerResponse)
def answer(req: AnswerRequest, db: Session = Depends(get_db)):
    try:
        return service.answer(db, req)
    except ValueError as e:  # 잘못된 종목·날짜 → 400 (Spring의 @ExceptionHandler로 400을 돌려주는 것과 같다)
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/history", response_model=HistoryResponse)
def history(db: Session = Depends(get_db)):
    return service.history(db)
