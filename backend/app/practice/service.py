"""Service. Spring의 @Service에 해당한다.

타임머신 연습장: 과거 어느 날로 돌아가 "그날까지 알 수 있던 정보"만 보고 6개월 뒤를 예상해 본다.
돈을 잃지 않고 판단을 연습하는 기출문제다. 매수·매도 권유가 아니라 "내 판단 습관"을 돌아보는 도구다.

- 문제(get_question): 주가가 오래 저장된 종목 중 하나와 날짜를 무작위로 고른다.
  그날까지의 차트(2년), 주가 흐름 숫자, 그때 나와 있던 사업보고서 기준 PER·PBR·실적만 준다.
  사업보고서는 보통 다음 해 3월 말에 나오므로, 4월 전이면 2년 전 해까지만 "알 수 있던 실적"으로 본다.
- 답(answer): 결과는 서버가 계산한다 (화면이 미리 알 수 없게). 6개월(126거래일) 뒤 등락률이
  +5% 이상이면 "올랐다", -5% 이하면 "내렸다", 그 사이면 "비슷했다". 같은 기간 시장 지수와도 비교한다.
  답과 결과는 마이데이터(my_record, kind=timemachine_guess)에 저장한다.
- 기록(history): 맞힌 비율과, 이유별로 얼마나 맞았는지 (예: "PER이 낮아서"를 고른 문제의 정답률).
"""
import json
import random
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core import fetch_log
from app.mydata import repository as mydata_repository
from app.mydata.models import MyRecord
from app.practice import client, repository
from app.practice.models import IndexPrice
from app.practice.schemas import (
    AnswerRequest,
    AnswerResponse,
    Fact,
    HistoryItem,
    HistoryResponse,
    Option,
    QuestionResponse,
    ReasonStat,
    YearRow,
)
from app.stock import repository as stock_repository
from app.stock.schemas import PriceResponse
from app.valuation import repository as valuation_repository
from app.valuation import service as valuation_service

KIND = "timemachine_guess"
QUESTION = "이날로부터 6개월 뒤, 이 종목은 어떻게 됐을까요?"
HORIZON = 126  # 거래일 (약 6개월)
BAND = 5.0  # ±5% 안이면 "비슷했다"
LOOKBACK_DAYS = 400  # 문제 날짜 앞으로 최소 이만큼(1년 넘게) 주가가 있어야 흐름 숫자를 만든다
CHART_DAYS = 730  # 화면에 보여줄 과거 차트 (2년)
INDEX = {"KOSPI": ("KS11", "코스피"), "KOSDAQ": ("KQ11", "코스닥")}

GUESSES = [Option(key="up", label="올랐다 (+5% 이상)"), Option(key="flat", label="비슷했다 (±5%)"), Option(key="down", label="내렸다 (-5% 이하)")]
REASONS = [
    Option(key="cheap", label="PER·PBR이 낮아 보여서"),
    Option(key="pricey", label="PER·PBR이 높아 보여서"),
    Option(key="growing", label="실적이 좋아지고 있어서"),
    Option(key="shrinking", label="실적이 나빠지고 있어서"),
    Option(key="uptrend", label="주가가 오르는 흐름이라"),
    Option(key="downtrend", label="주가가 내리는 흐름이라"),
    Option(key="too_high", label="이미 많이 올라서"),
    Option(key="too_low", label="이미 많이 내려서"),
    Option(key="gut", label="그냥 감으로"),
]
OUTCOME_LABEL = {"up": "올랐다", "flat": "비슷했다", "down": "내렸다"}


# ── 문제 ────────────────────────────────────────────────


def get_question(db: Session, code: str | None = None) -> QuestionResponse:
    latest_start = date.today() - timedelta(days=LOOKBACK_DAYS + 200)
    if code:
        candidates = [code]
    else:
        candidates = [
            c
            for c in stock_repository.find_codes_with_prices_before(db, latest_start)
            if (s := stock_repository.find_stock(db, c)) and s.market != "ETF"  # ETF는 실적·PER이 없어서 뺀다
        ]
    random.shuffle(candidates)
    for c in candidates:
        prices = stock_repository.find_prices(db, c, date(2000, 1, 1))
        picks = [
            i
            for i in range(len(prices) - HORIZON)
            if prices[i].date >= prices[0].date + timedelta(days=LOOKBACK_DAYS)
        ]
        if picks:
            return _question(db, c, prices, random.choice(picks))
    return QuestionResponse(available=False, message="연습할 만큼 오래된 주가가 저장된 종목이 아직 없어요.")


def _question(db: Session, code: str, prices: list, i: int) -> QuestionResponse:
    stock = stock_repository.find_stock(db, code)
    fundamental = valuation_repository.find(db, code)
    as_of = prices[i].date
    shown = [p for p in prices[: i + 1] if p.date >= as_of - timedelta(days=CHART_DAYS)]
    value_facts, years = _known_financials(db, code, as_of, prices[i].close)
    return QuestionResponse(
        available=True,
        code=code,
        name=stock.name,
        market=stock.market,
        industry=fundamental.industry_name if fundamental else None,
        as_of=as_of,
        prices=[PriceResponse.model_validate(p) for p in shown],
        price_facts=_price_facts(prices, i),
        value_facts=value_facts,
        years=years,
        guesses=GUESSES,
        reasons=REASONS,
    )


def _pct(a: float, b: float) -> float:
    return (a / b - 1) * 100 if b else 0.0


def _fmt(v: float) -> str:
    return f"{v:+.1f}%"


def _tone(v: float) -> str:
    return "up" if v > 0 else "down" if v < 0 else ""


def _price_facts(prices: list, i: int) -> list[Fact]:
    close = prices[i].close
    facts = []
    for label, n in (("최근 1개월", 21), ("최근 3개월", 63), ("최근 1년", 250)):
        if i - n >= 0:
            v = _pct(close, prices[i - n].close)
            facts.append(Fact(label=label, value=_fmt(v), tone=_tone(v)))
    year = prices[max(0, i - 250) : i + 1]
    high, low = max(p.high for p in year), min(p.low for p in year)
    pos = (close - low) / (high - low) * 100 if high > low else 50
    facts.append(
        Fact(
            label="1년 중 위치",
            value=f"{pos:.0f}%",
            hint="1년 최저가를 0%, 최고가를 100%로 봤을 때 지금 가격의 위치예요. 높을수록 1년 최고가 가까이에 있어요.",
        )
    )
    above = []
    for n in (20, 60, 120):
        if i - n + 1 >= 0:
            ma = sum(p.close for p in prices[i - n + 1 : i + 1]) / n
            above.append(f"{n}일선 {'위' if close >= ma else '아래'}")
    if above:
        facts.append(
            Fact(
                label="이동평균선",
                value=" · ".join(above),
                hint="이동평균선은 최근 n일 종가의 평균이에요. 주가가 선 위에 있으면 최근 평균보다 비싸게 거래되고 있다는 뜻이에요.",
            )
        )
    return facts


def _known_financials(db: Session, code: str, as_of: date, close: int) -> tuple[list[Fact], list[YearRow]]:
    """그날 이미 나와 있던 사업보고서만 쓴다 (사업보고서는 보통 다음 해 3월 말에 나온다)."""
    last_known = as_of.year - 1 if as_of.month >= 4 else as_of.year - 2
    if not valuation_repository.find_annual(db, code):
        try:  # 연간 실적을 아직 안 받은 종목이면 한 번 받아 둔다 (OpenDART 10년치, 일주일에 한 번만)
            valuation_service.get_overview(db, code)
        except Exception as e:
            db.rollback()
            print(f"  타임머신용 실적 수집 실패({code}): {e!r}")
    annual = [a for a in valuation_repository.find_annual(db, code) if a.year <= last_known]
    annual.sort(key=lambda a: a.year)
    years = [
        YearRow(
            year=a.year,
            revenue=None if a.revenue is None else round(a.revenue / 1e8),
            operating_profit=None if a.operating_profit is None else round(a.operating_profit / 1e8),
            net_income=None if a.net_income is None else round(a.net_income / 1e8),
        )
        for a in annual[-3:]
    ]
    facts: list[Fact] = []
    if annual:
        last = annual[-1]
        shares = valuation_service.split_adjusted_shares(db, code).get(last.year)
        if shares and last.net_income is not None:
            if last.net_income > 0:
                per = close * shares / last.net_income
                facts.append(Fact(label=f"PER ({last.year}년 이익 기준)", value=f"{per:.1f}배",
                                  hint="주가가 1년 이익의 몇 배인지. 낮을수록 이익에 비해 싸게 거래되는 편이에요(업종마다 보통 수준이 달라요)."))
            else:
                facts.append(Fact(label=f"PER ({last.year}년 이익 기준)", value="적자라 계산 안 됨", tone="down"))
        if shares and last.equity and last.equity > 0:
            pbr = close * shares / last.equity
            facts.append(Fact(label=f"PBR ({last.year}년 자본 기준)", value=f"{pbr:.2f}배",
                              hint="주가가 회사 순자산의 몇 배인지. 1배보다 낮으면 장부상 재산보다 싸게 거래되는 편이에요."))
    return facts, years


# ── 답 ──────────────────────────────────────────────────


def answer(db: Session, req: AnswerRequest) -> AnswerResponse:
    stock = stock_repository.find_stock(db, req.code)
    if stock is None:
        raise ValueError("종목을 찾을 수 없어요.")
    prices = stock_repository.find_prices(db, req.code, date(2000, 1, 1))
    i = next((k for k, p in enumerate(prices) if p.date == req.as_of), None)
    if i is None or i + HORIZON >= len(prices):
        raise ValueError("이 날짜로는 결과를 계산할 수 없어요.")
    start, end = prices[i], prices[i + HORIZON]
    ret = _pct(end.close, start.close)
    after = prices[i + 1 : i + HORIZON + 1]
    max_up = max(_pct(p.close, start.close) for p in after)
    max_down = min(_pct(p.close, start.close) for p in after)
    outcome = "up" if ret >= BAND else "down" if ret <= -BAND else "flat"
    correct = outcome == req.guess

    index_code, index_name = INDEX.get(stock.market, INDEX["KOSPI"])
    index_ret = _index_return(db, index_code, start.date, end.date)
    guess_label = next((g.label for g in GUESSES if g.key == req.guess), req.guess)
    comment = _comment(ret, index_ret, index_name, max_up, max_down, correct)

    reasons = [r for r in req.reasons if any(o.key == r for o in REASONS)]
    mydata_repository.save(
        db,
        MyRecord(
            kind=KIND,
            stock_code=req.code,
            question=QUESTION,
            answer=req.guess,
            answer_label=guess_label,
            memo=req.memo.strip(),
            context_json=json.dumps(
                {
                    "name": stock.name,
                    "as_of": start.date.isoformat(),
                    "end_date": end.date.isoformat(),
                    "horizon_days": HORIZON,
                    "reasons": reasons,
                    "outcome": outcome,
                    "correct": correct,
                    "return_pct": round(ret, 2),
                    "index_return_pct": None if index_ret is None else round(index_ret, 2),
                    "max_up_pct": round(max_up, 2),
                    "max_down_pct": round(max_down, 2),
                },
                ensure_ascii=False,
            ),
            created_at=datetime.now(),
        ),
    )
    db.commit()
    chart = [p for p in prices[: i + HORIZON + 1] if p.date >= start.date - timedelta(days=CHART_DAYS)]
    return AnswerResponse(
        name=stock.name,
        as_of=start.date,
        end_date=end.date,
        guess_label=guess_label,
        outcome=outcome,
        outcome_label=OUTCOME_LABEL[outcome],
        correct=correct,
        return_pct=round(ret, 2),
        index_name=index_name,
        index_return_pct=None if index_ret is None else round(index_ret, 2),
        max_up_pct=round(max_up, 2),
        max_down_pct=round(max_down, 2),
        comment=comment,
        prices=[PriceResponse.model_validate(p) for p in chart],
    )


def _comment(ret: float, index_ret: float | None, index_name: str, max_up: float, max_down: float, correct: bool) -> str:
    parts = [f"6개월 동안 {_fmt(ret)} 움직였어요."]
    if index_ret is not None:
        diff = ret - index_ret
        rel = "시장보다 잘한 편" if diff >= BAND else "시장보다 못한 편" if diff <= -BAND else "시장과 비슷한 편"
        parts.append(f"같은 기간 {_josa(index_name)} {_fmt(index_ret)}여서 {rel}이에요.")
    if max_down <= -10 and ret > 0:
        parts.append(f"결국 올랐지만 중간에 한때 {_fmt(max_down)}까지 내려가기도 했어요. 그 흔들림을 견뎌야 했던 셈이에요.")
    elif max_up >= 10 and ret < 0:
        parts.append(f"결국 내렸지만 중간에 한때 {_fmt(max_up)}까지 오르기도 했어요.")
    parts.append("예상이 맞았어요." if correct else "이번엔 예상과 달랐어요. 어떤 정보를 더 봤으면 좋았을지 생각해 보세요.")
    return " ".join(parts)


def _josa(word: str) -> str:
    """받침이 있으면 '은', 없으면 '는' (코스닥은 / 코스피는)."""
    last = word[-1]
    has_final = "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 != 0
    return word + ("은" if has_final else "는")


def _index_return(db: Session, index_code: str, start: date, end: date) -> float | None:
    _refresh_index(db, index_code, end)
    rows = repository.find_index_since(db, index_code, start - timedelta(days=10))
    before_start = [r for r in rows if r.date <= start]
    before_end = [r for r in rows if r.date <= end]
    if not before_start or not before_end:
        return None
    return _pct(before_end[-1].close, before_start[-1].close)


def _refresh_index(db: Session, index_code: str, needed: date) -> None:
    latest = repository.find_index_latest_date(db, index_code)
    key = f"index:{index_code}"
    if latest and latest >= needed:
        return
    if fetch_log.is_fresh(db, key, 720):
        return
    try:
        start = latest - timedelta(days=7) if latest else date.today() - timedelta(days=365 * 10 + 10)
        rows = client.fetch_index(index_code, start)
        repository.save_index(db, [IndexPrice(index_code=index_code, date=d, close=c) for d, c in rows])
        fetch_log.mark_fetched(db, key)
        db.commit()
    except Exception as e:  # 지수를 못 받아도 결과는 보여준다
        db.rollback()
        print(f"  지수 수집 실패({index_code}): {e!r}")


# ── 기록 ────────────────────────────────────────────────


def history(db: Session, limit: int = 30) -> HistoryResponse:
    records = mydata_repository.find(db, KIND, None, None)
    rows = [(r, json.loads(r.context_json or "{}")) for r in records]
    stats = {o.key: ReasonStat(key=o.key, label=o.label, total=0, correct=0) for o in REASONS}
    for _, ctx in rows:
        for key in ctx.get("reasons", []):
            if key in stats:
                stats[key].total += 1
                stats[key].correct += 1 if ctx.get("correct") else 0
    by_guess = []
    for g in GUESSES:
        mine = [ctx for r, ctx in rows if r.answer == g.key]
        if mine:
            by_guess.append(
                ReasonStat(key=g.key, label=OUTCOME_LABEL[g.key], total=len(mine), correct=sum(1 for c in mine if c.get("correct")))
            )
    by_reason = sorted([s for s in stats.values() if s.total], key=lambda s: -s.total)
    return HistoryResponse(
        total=len(rows),
        correct=sum(1 for _, ctx in rows if ctx.get("correct")),
        by_guess=by_guess,
        by_reason=by_reason,
        lines=_history_lines(rows, by_guess, by_reason),
        items=[
            HistoryItem(
                created_at=r.created_at,
                code=r.stock_code,
                name=ctx.get("name", r.stock_code or ""),
                as_of=ctx.get("as_of", ""),
                guess_label=r.answer_label,
                outcome_label=OUTCOME_LABEL.get(ctx.get("outcome", ""), "-"),
                correct=bool(ctx.get("correct")),
                return_pct=ctx.get("return_pct", 0.0),
            )
            for r, ctx in rows[:limit]
        ],
    )


def _history_lines(rows: list, by_guess: list[ReasonStat], by_reason: list[ReasonStat]) -> list[str]:
    """한 줄 돌아보기. 문제가 적을 때는 우연이 크다는 말을 먼저 한다."""
    if not rows:
        return []
    total, correct = len(rows), sum(1 for _, c in rows if c.get("correct"))
    out = [f"타임머신 문제 {total}개 중 {correct}개를 맞혔어요 ({correct / total * 100:.0f}%). 세 가지 중 하나를 찍으면 평균 33%쯤 맞아요."]
    if by_guess:
        most = max(by_guess, key=lambda g: g.total)
        if most.total >= 2 and most.total / total >= 0.6:
            out.append(f"'{most.label}'로 예상한 게 {most.total}번으로 가장 많아요. 한쪽으로 쏠리는 습관일 수 있어요.")
    sure = [r for r in by_reason if r.total >= 3]
    if sure:
        rate = lambda r: r.correct / r.total  # noqa: E731
        best, worst = max(sure, key=rate), min(sure, key=rate)
        if rate(best) > rate(worst):  # 이유마다 차이가 있을 때만 말한다
            out.append(f"가장 잘 맞은 이유: '{best.label}' ({best.correct}/{best.total}).")
            out.append(f"가장 덜 맞은 이유: '{worst.label}' ({worst.correct}/{worst.total}). 이 이유로 판단할 땐 다른 정보도 함께 보세요.")
    gut = next((r for r in by_reason if r.key == "gut"), None)
    if gut and gut.total >= 3:
        out.append(f"'그냥 감으로'는 {gut.total}번 중 {gut.correct}번 맞았어요. 이유를 고른 문제와 비교해 보세요.")
    if total < 10:
        out.append("문제가 10개는 넘어야 습관이 보이기 시작해요.")
    return out
