"""Service. Spring의 @Service에 해당한다.

오늘의 읽기 퀴즈: 내 관심종목의 실제 공시·지표·리포트로 "읽는 법"을 묻는 문제를 하루 3개 낸다.
- 오늘의 문제(today): 날짜로 정한 난수라서 같은 날에는 같은 문제가 나온다. 유형이 겹치지 않게 3개.
- 더 풀기(extra): 아무 유형·종목에서 새 문제 하나.
- 채점(answer): qid(유형|종목|참조)로 문제를 다시 만들어 정답과 비교한다 (화면이 정답을 미리 알 수 없게).
  답은 마이데이터(my_record, kind=quiz)에 저장한다. 같은 날 같은 문제를 또 내면 처음 결과를 돌려준다.
- 기록(stats): 맞힌 수, 연속 학습일, 유형별 정답률, 최근 틀린 문제(다시 볼 것).
"""
import json
import random
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.mydata import repository as mydata_repository
from app.mydata.models import MyRecord
from app.quiz import questions
from app.quiz.questions import TYPES, Item
from app.quiz.schemas import (
    AnswerRequest,
    QuizOption,
    QuizQuestion,
    QuizResult,
    StatsResponse,
    TodayResponse,
    TypeStat,
    WrongItem,
)
from app.stock import repository as stock_repository

KIND = "quiz"
DAILY = 3


def _candidates(db: Session) -> list[str]:
    """문제에 쓸 종목: 관심종목(ETF 제외)만. 사용자가 관심 둔 회사로 배워야 기억에 남는다 (2026-11-25 사용자 요청)."""
    watched = [s.code for s in stock_repository.find_watched_stocks(db) if s.market != "ETF"]
    return watched


def _make(db: Session, rng: random.Random, types: list[str], codes: list[str], skip: set[str]) -> Item | None:
    for qtype in types:
        for code in codes:
            try:
                item = questions.build(db, qtype, code, None, rng)
            except Exception as e:  # 한 종목 데이터가 이상해도 다른 문제를 낸다
                db.rollback()
                print(f"  퀴즈 문제 만들기 실패({qtype}, {code}): {e!r}")
                item = None
            if item and item.qid not in skip:
                return item
    return None


def today(db: Session) -> TodayResponse:
    day = date.today()
    rng = random.Random(f"quiz-{day.isoformat()}")
    codes = _candidates(db)
    types = list(TYPES)
    rng.shuffle(types)
    items: list[Item] = []
    for qtype in types:
        if len(items) >= DAILY:
            break
        shuffled = codes[:]
        rng.shuffle(shuffled)
        item = _make(db, rng, [qtype], shuffled, {i.qid for i in items})
        if item:
            items.append(item)
    answered = _answered_today(db)
    out = [_to_question(i, answered.get(i.qid)) for i in items]
    return TodayResponse(day=day, questions=out, done=sum(1 for q in out if q.result))


def extra(db: Session, exclude: list[str]) -> QuizQuestion | None:
    rng = random.Random()
    codes = _candidates(db)
    rng.shuffle(codes)
    types = list(TYPES)
    rng.shuffle(types)
    item = _make(db, rng, types, codes, set(exclude))
    return _to_question(item, None) if item else None


def answer(db: Session, req: AnswerRequest) -> QuizResult:
    item = _rebuild(db, req.qid)
    if item is None:
        raise ValueError("이 문제를 다시 만들 수 없어요 (데이터가 바뀌었을 수 있어요).")
    done = _answered_today(db).get(req.qid)
    if done:  # 오늘 이미 푼 문제면 처음 낸 답의 결과를 돌려준다 (다시 저장하지 않는다)
        return _result(item, done.chosen_key)
    result = _result(item, req.choice)
    chosen_label = dict(item.options).get(req.choice, req.choice)
    mydata_repository.save(
        db,
        MyRecord(
            kind=KIND,
            stock_code=item.code,
            question=item.prompt,
            answer=req.choice,
            answer_label=chosen_label[:60],
            memo="",
            context_json=json.dumps(
                {
                    "qid": item.qid,
                    "type": item.type,
                    "name": item.name,
                    "day": date.today().isoformat(),
                    "correct": result.correct,
                    "correct_key": item.correct,
                    "correct_label": result.correct_label,
                },
                ensure_ascii=False,
            ),
            created_at=datetime.now(),
        ),
    )
    db.commit()
    return result


def stats(db: Session) -> StatsResponse:
    rows = [(r, json.loads(r.context_json or "{}")) for r in mydata_repository.find(db, KIND, None, None)]
    by_type = []
    for key, label in TYPES.items():
        mine = [c for _, c in rows if c.get("type") == key]
        if mine:
            by_type.append(TypeStat(type=key, label=label, total=len(mine), correct=sum(1 for c in mine if c.get("correct"))))
    days = sorted({c.get("day") for _, c in rows if c.get("day")}, reverse=True)
    streak = 0
    expect = date.today()
    if days and days[0] != expect.isoformat():
        expect -= timedelta(days=1)  # 오늘 아직 안 풀었으면 어제까지 이어졌는지 본다
    for d in days:
        if d == expect.isoformat():
            streak += 1
            expect -= timedelta(days=1)
        else:
            break
    wrong = [
        WrongItem(
            created_at=r.created_at,
            type_label=TYPES.get(c.get("type", ""), ""),
            stock_name=c.get("name", ""),
            prompt=r.question,
            correct_label=c.get("correct_label", ""),
        )
        for r, c in rows
        if not c.get("correct")
    ][:5]
    total, correct = len(rows), sum(1 for _, c in rows if c.get("correct"))
    return StatsResponse(
        total=total,
        correct=correct,
        streak=streak,
        days=len(days),
        by_type=by_type,
        recent_wrong=wrong,
        lines=_lines(total, correct, streak, by_type),
    )


def _lines(total: int, correct: int, streak: int, by_type: list[TypeStat]) -> list[str]:
    if total == 0:
        return []
    out = [f"지금까지 {total}문제 중 {correct}문제를 맞혔어요 ({correct / total * 100:.0f}%)."]
    if streak >= 2:
        out.append(f"{streak}일 연속으로 풀고 있어요.")
    sure = [t for t in by_type if t.total >= 3]
    if sure:
        weak = min(sure, key=lambda t: t.correct / t.total)
        if weak.correct / weak.total < 0.7:
            out.append(f"'{weak.label}' 유형이 아직 어려워요 ({weak.correct}/{weak.total}). 도움말에서 그 부분을 한 번 읽어 보세요.")
    return out


# ── 내부 ──────────────────────────────────────────────


def _rebuild(db: Session, qid: str) -> Item | None:
    parts = qid.split("|")
    if len(parts) != 3:
        return None
    qtype, code, ref = parts
    # 보기 순서는 qid로 정한 난수라 문제를 다시 만들어도 같다
    return questions.build(db, qtype, code, ref or None, random.Random(qid)) if qtype in TYPES else None


def _answered_today(db: Session) -> dict[str, QuizResult]:
    """오늘 푼 문제의 결과 (qid → 결과). 문제를 다시 만들지 않고 저장된 값으로 만든다."""
    out: dict[str, QuizResult] = {}
    today_iso = date.today().isoformat()
    for r in mydata_repository.find(db, KIND, None, None):
        c = json.loads(r.context_json or "{}")
        if c.get("day") != today_iso or c.get("qid") in out:
            continue
        out[c["qid"]] = QuizResult(
            correct=bool(c.get("correct")),
            chosen_key=r.answer,
            correct_key=c.get("correct_key", ""),
            correct_label=c.get("correct_label", ""),
            explanation="",
        )
    return out


def _to_question(item: Item, done: QuizResult | None) -> QuizQuestion:
    q = QuizQuestion(
        qid=item.qid,
        type=item.type,
        type_label=TYPES[item.type],
        stock_code=item.code,
        stock_name=item.name,
        prompt=item.prompt,
        context=item.context,
        options=[QuizOption(key=k, label=lab) for k, lab in item.options],
    )
    if done:
        q.result = _result(item, done.chosen_key)  # 해설까지 다시 채운다
    return q


def _result(item: Item, choice: str) -> QuizResult:
    labels = dict(item.options)
    return QuizResult(
        correct=choice == item.correct,
        chosen_key=choice,
        correct_key=item.correct,
        correct_label=labels.get(item.correct, item.correct),
        explanation=item.explanation,
        checks=item.checks,
        note=item.note,
        link=item.link,
    )
