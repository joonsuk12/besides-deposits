"""Service. Spring의 @Service에 해당한다.

답을 저장할 때 그때의 상황(최근 종가와 그 날짜)을 서버가 붙여 둔다.
나중에 "답한 뒤 주가가 어떻게 됐나"를 계산할 수 있게 하려는 것이다 (지금은 저장만, 가공은 다음 단계).
"""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.mydata import repository
from app.mydata.models import MyRecord
from app.mydata.schemas import MyRecordCreate, MyRecordResponse
from app.stock import repository as stock_repository


def create(db: Session, req: MyRecordCreate) -> MyRecordResponse:
    context = dict(req.context)
    if req.stock_code:
        recent = stock_repository.find_recent_prices(db, req.stock_code, 1)
        if recent:
            context["close"] = recent[0].close
            context["close_date"] = recent[0].date.isoformat()
    row = repository.save(
        db,
        MyRecord(
            kind=req.kind,
            stock_code=req.stock_code,
            question=req.question,
            answer=req.answer,
            answer_label=req.answer_label,
            memo=req.memo.strip(),
            context_json=json.dumps(context, ensure_ascii=False),
            created_at=datetime.now(),
        ),
    )
    db.commit()
    return _to_response(row)


def find(db: Session, kind: str | None, stock_code: str | None, limit: int | None) -> list[MyRecordResponse]:
    return [_to_response(r) for r in repository.find(db, kind, stock_code, limit)]


def _to_response(r: MyRecord) -> MyRecordResponse:
    return MyRecordResponse(
        id=r.id,
        kind=r.kind,
        stock_code=r.stock_code,
        question=r.question,
        answer=r.answer,
        answer_label=r.answer_label,
        memo=r.memo,
        context=json.loads(r.context_json or "{}"),
        created_at=r.created_at,
    )
