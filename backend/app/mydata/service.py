"""Service. Spring의 @Service에 해당한다.

답을 저장할 때 그때의 상황(최근 종가와 그 날짜)을 서버가 붙여 둔다.
insights()는 그 기록을 가공한다: 위험 신호를 보고 "걱정돼요/괜찮아 보여요"라고 답한 종목이 그 뒤 어떻게 움직였는지.
좋고 나쁨을 판정하지 않고 "내가 그때 이렇게 생각했고, 그 뒤 이렇게 됐다"는 사실만 보여준다 (매수·매도 권유 없음).
"""
import json
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.mydata import repository
from app.mydata.models import MyRecord
from app.mydata.schemas import AnswerGroup, InsightsResponse, MyRecordCreate, MyRecordResponse, RiskReactionItem
from app.risk.service import CHECK_TITLES
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


RISK_KIND = "risk_reaction"
RISK_ANSWERS = {"fine": "괜찮아 보여요", "more": "더 알아볼래요", "worried": "걱정돼요"}
MIN_DAYS = 7  # 답한 지 일주일은 지나야 "그 뒤"를 말할 수 있다


def insights(db: Session) -> InsightsResponse:
    items = [_risk_item(db, r) for r in repository.find(db, RISK_KIND, None, None)]
    groups = []
    for key, label in RISK_ANSWERS.items():
        mine = [i for i in items if i.answer == key]
        if not mine:
            continue
        old = [i.change_pct for i in mine if i.change_pct is not None and (i.days or 0) >= MIN_DAYS]
        groups.append(
            AnswerGroup(
                answer=key,
                label=label,
                count=len(mine),
                avg_change_pct=round(sum(old) / len(old), 2) if old else None,
                counted=len(old),
            )
        )
    return InsightsResponse(
        lines=_lines(items, groups),
        risk_items=items,
        risk_groups=groups,
        total_records=len(repository.find(db, None, None, None)),
    )


def _risk_item(db: Session, r: MyRecord) -> RiskReactionItem:
    ctx = json.loads(r.context_json or "{}")
    stock = stock_repository.find_stock(db, r.stock_code) if r.stock_code else None
    recent = stock_repository.find_recent_prices(db, r.stock_code, 1) if r.stock_code else []
    close_then, close_now = ctx.get("close"), (recent[0].close if recent else None)
    then_date = ctx.get("close_date")
    change = round((close_now / close_then - 1) * 100, 2) if close_then and close_now else None
    days = (date.today() - date.fromisoformat(then_date)).days if then_date else None
    return RiskReactionItem(
        id=r.id,
        created_at=r.created_at,
        stock_code=r.stock_code or "",
        name=stock.name if stock else (r.stock_code or ""),
        answer=r.answer,
        answer_label=r.answer_label,
        memo=r.memo,
        flagged=[CHECK_TITLES.get(k, k) for k in ctx.get("flagged", [])],
        close_then=close_then,
        close_then_date=then_date,
        close_now=close_now,
        close_now_date=recent[0].date.isoformat() if recent else None,
        change_pct=change,
        days=days,
    )


def _lines(items: list[RiskReactionItem], groups: list[AnswerGroup]) -> list[str]:
    """한 줄 돌아보기. 숫자가 충분하지 않으면 말을 아낀다."""
    if not items:
        return []
    out = [f"위험 신호를 보고 생각을 {len(items)}번 남겼어요."]
    for g in groups:
        if g.avg_change_pct is None:
            out.append(f"'{g.label}'라고 답한 {g.count}번은 아직 일주일이 안 지나서 그 뒤를 보기엔 일러요.")
        else:
            word = "올랐어요" if g.avg_change_pct > 0 else "내렸어요" if g.avg_change_pct < 0 else "그대로예요"
            out.append(f"'{g.label}'라고 답한 종목 {g.counted}개는 그 뒤 평균 {g.avg_change_pct:+.1f}% {word}.")
    flagged = [i for i in items if i.flagged]
    if flagged:
        worried = sum(1 for i in flagged if i.answer == "worried")
        out.append(f"🔴·🟡 신호가 있던 {len(flagged)}번 중 '걱정돼요'라고 답한 건 {worried}번이에요.")
    if len(items) < 5:
        out.append("기록이 5개는 넘어야 습관이 보이기 시작해요. 짧은 기간의 주가는 우연도 커요.")
    return out
