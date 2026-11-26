"""Controller. Spring의 @RestController에 해당한다.

- GET  /quiz/today                 오늘의 3문제 (오늘 이미 푼 문제는 결과까지)
- GET  /quiz/extra?exclude=qid,…   더 풀기: 새 문제 하나
- POST /quiz/answer                답 내기 → 정답·해설 (마이데이터에 저장)
- GET  /quiz/stats                 맞힌 수, 연속 학습일, 유형별 정답률, 최근 틀린 문제
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.quiz import service
from app.quiz.schemas import AnswerRequest, QuizQuestion, QuizResult, StatsResponse, TodayResponse

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/today", response_model=TodayResponse)
def today(db: Session = Depends(get_db)):
    return service.today(db)


@router.get("/extra", response_model=QuizQuestion | None)
def extra(exclude: str = "", db: Session = Depends(get_db)):
    return service.extra(db, [q for q in exclude.split(",") if q])


@router.post("/answer", response_model=QuizResult)
def answer(req: AnswerRequest, db: Session = Depends(get_db)):
    try:
        return service.answer(db, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)):
    return service.stats(db)
