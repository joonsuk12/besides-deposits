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

from app.core import fetch_log, krx
from app.mydata import repository as mydata_repository
from app.mydata.models import MyRecord
from app.practice import client, repository
from app.practice.models import BondYield, IndexPrice, IndexValuation, SectorMember
from app.practice.schemas import (
    AnswerRequest,
    AnswerResponse,
    Fact,
    HistoryItem,
    HistoryResponse,
    Option,
    QuestionResponse,
    ReasonStat,
    SectorGuide,
    YearRow,
)
from app.stock import repository as stock_repository
from app.stock.schemas import PriceResponse
from app.valuation import repository as valuation_repository
from app.valuation import focus
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
    industry = fundamental.industry_name if fundamental else None
    as_of = prices[i].date
    shown = [p for p in prices[: i + 1] if p.date >= as_of - timedelta(days=CHART_DAYS)]
    annual = _known_annual(db, code, as_of)
    last = annual[-1] if annual else None
    # 그때 적자였으면 PER 대신 PBR을 보라고 안내가 바뀐다 (focus.decide는 eps 부호만 본다)
    guide = focus.decide(industry, last.net_income if last and last.net_income is not None else None)
    years = _year_rows(db, code, annual, prices)
    stock_per, stock_pbr = _stock_multiples(db, code, annual, prices[i].close)
    sector_facts, krx_sector = _sector_facts(db, code, stock.market, as_of, stock_per, stock_pbr, guide.focus)
    rate_key = any("금리" in a for a in guide.also)  # 업종 가이드가 금리를 "함께 볼 것"으로 꼽으면 ⭐
    return QuestionResponse(
        available=True,
        code=code,
        name=stock.name,
        market=stock.market,
        industry=industry,
        as_of=as_of,
        prices=[PriceResponse.model_validate(p) for p in shown],
        sector=SectorGuide(
            name=industry or "업종 정보 없음",
            focus=guide.focus,
            title=guide.title,
            reason=guide.reason,
            also=list(guide.also),
            caution=guide.caution,
        ),
        market_facts=_market_facts(db, stock.market, prices, i),
        price_facts=_price_facts(prices, i),
        value_facts=_value_facts(db, code, annual, years, prices[i].close, guide.focus),
        growth_facts=_growth_facts(years, guide.focus),
        krx_sector=krx_sector,
        sector_facts=sector_facts,
        rate_facts=_rate_facts(db, as_of, rate_key),
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
    vols = [p.volume for p in year if p.volume]
    recent = [p.volume for p in prices[max(0, i - 19) : i + 1] if p.volume]
    if vols and recent:
        ratio = (sum(recent) / len(recent)) / (sum(vols) / len(vols))
        facts.append(
            Fact(
                label="최근 거래량",
                value=f"1년 평균의 {ratio:.1f}배",
                tone="up" if ratio >= 1.5 else "",
                hint="최근 20일 평균 거래량을 1년 평균과 비교했어요. 크게 늘었다면 관심이 몰리고 있다는 뜻이에요(좋고 나쁨은 몰라요).",
            )
        )
    moves = [abs(_pct(b.close, a.close)) for a, b in zip(year, year[1:]) if a.close]
    if moves:
        facts.append(
            Fact(
                label="하루 평균 움직임",
                value=f"±{sum(moves) / len(moves):.1f}%",
                hint="지난 1년 동안 하루에 평균 이만큼 오르내렸어요. 클수록 주가가 출렁이는 종목이에요.",
            )
        )
    return facts


def _market_facts(db: Session, market: str, prices: list, i: int) -> list[Fact]:
    """그때 시장 전체는 어땠나. 종목만 보면 시장 분위기를 놓치기 쉽다."""
    index_code, index_name = INDEX.get(market, INDEX["KOSPI"])
    as_of = prices[i].date
    _refresh_index(db, index_code, as_of)
    rows = [r for r in repository.find_index_since(db, index_code, as_of - timedelta(days=380)) if r.date <= as_of]
    if len(rows) < 2:
        return []

    def back(days: int) -> float | None:
        before = [r for r in rows if r.date <= as_of - timedelta(days=days)]
        return before[-1].close if before else None

    facts = []
    now = rows[-1].close
    for label, days in ((f"{index_name} 최근 3개월", 91), (f"{index_name} 최근 1년", 365)):
        base = back(days)
        if base:
            v = _pct(now, base)
            facts.append(Fact(label=label, value=_fmt(v), tone=_tone(v)))
    base = back(365)
    if base and i - 250 >= 0:
        diff = _pct(prices[i].close, prices[i - 250].close) - _pct(now, base)
        word = "시장보다 강했어요" if diff >= 5 else "시장보다 약했어요" if diff <= -5 else "시장과 비슷했어요"
        facts.append(
            Fact(
                label="1년 동안 이 종목은",
                value=f"{word} ({diff:+.0f}%p)",
                tone=_tone(diff) if abs(diff) >= 5 else "",
                hint="이 종목 1년 등락에서 시장 지수 1년 등락을 뺀 값이에요. 시장 전체가 오를 때 같이 오른 건지, 이 종목만 따로 움직였는지 볼 수 있어요.",
            )
        )
    return facts


def _known_annual(db: Session, code: str, as_of: date) -> list:
    """그날 이미 나와 있던 사업보고서만 쓴다 (사업보고서는 보통 다음 해 3월 말에 나온다)."""
    last_known = as_of.year - 1 if as_of.month >= 4 else as_of.year - 2
    if not valuation_repository.find_annual(db, code):
        try:  # 연간 실적을 아직 안 받은 종목이면 한 번 받아 둔다 (OpenDART 10년치, 일주일에 한 번만)
            valuation_service.get_overview(db, code)
        except Exception as e:
            db.rollback()
            print(f"  타임머신용 실적 수집 실패({code}): {e!r}")
    annual = [a for a in valuation_repository.find_annual(db, code) if a.year <= last_known]
    return sorted(annual, key=lambda a: a.year)


def _year_rows(db: Session, code: str, annual: list, prices: list) -> list[YearRow]:
    """최근 5년 실적 + 그해 마지막 거래일 종가로 계산한 PER·PBR (그 회사의 '평소 수준'을 보려고)."""
    shares = valuation_service.split_adjusted_shares(db, code)
    year_end: dict[int, int] = {}
    for p in prices:
        year_end[p.date.year] = p.close  # 날짜순이라 마지막 값이 그해 마지막 거래일
    rows = []
    for k, a in enumerate(annual):
        prev = annual[k - 1] if k > 0 and annual[k - 1].year == a.year - 1 else None
        sh, close = shares.get(a.year), year_end.get(a.year)
        rows.append(
            YearRow(
                year=a.year,
                revenue=None if a.revenue is None else round(a.revenue / 1e8),
                operating_profit=None if a.operating_profit is None else round(a.operating_profit / 1e8),
                net_income=None if a.net_income is None else round(a.net_income / 1e8),
                revenue_growth=round(_pct(a.revenue, prev.revenue), 1) if prev and a.revenue and prev.revenue else None,
                op_margin=round(a.operating_profit / a.revenue * 100, 1)
                if a.revenue and a.operating_profit is not None
                else None,
                roe=round(a.net_income / a.equity * 100, 1)
                if a.equity and a.equity > 0 and a.net_income is not None
                else None,
                per=round(close * sh / a.net_income, 1) if sh and close and a.net_income and a.net_income > 0 else None,
                pbr=round(close * sh / a.equity, 2) if sh and close and a.equity and a.equity > 0 else None,
            )
        )
    return rows[-5:]


def _stock_multiples(db: Session, code: str, annual: list, close: int) -> tuple[float | None, float | None]:
    """그날 종가 기준 PER·PBR (그때 나와 있던 마지막 사업보고서). 적자면 PER은 None."""
    if not annual:
        return None, None
    last = annual[-1]
    shares = valuation_service.split_adjusted_shares(db, code).get(last.year)
    per = close * shares / last.net_income if shares and last.net_income and last.net_income > 0 else None
    pbr = close * shares / last.equity if shares and last.equity and last.equity > 0 else None
    return per, pbr


def _value_facts(db: Session, code: str, annual: list, years: list[YearRow], close: int, sector_focus: str) -> list[Fact]:
    facts: list[Fact] = []
    if not annual:
        return facts
    last = annual[-1]
    shares = valuation_service.split_adjusted_shares(db, code).get(last.year)
    past_per = [y.per for y in years if y.per]
    past_pbr = [y.pbr for y in years if y.pbr]
    if shares and last.net_income is not None:
        if last.net_income > 0:
            per = close * shares / last.net_income
            facts.append(
                Fact(
                    label=f"PER ({last.year}년 이익 기준)",
                    value=f"{per:.1f}배",
                    key=sector_focus in ("per", "both"),
                    hint="주가가 1년 이익의 몇 배인지. 낮을수록 이익에 비해 싸게 거래되는 편이에요(업종마다 보통 수준이 달라요).",
                )
            )
            if len(past_per) >= 2:
                facts.append(_band("평소 PER", per, past_per))
        else:
            facts.append(Fact(label=f"PER ({last.year}년 이익 기준)", value="적자라 계산 안 됨", tone="down"))
    if shares and last.equity and last.equity > 0:
        pbr = close * shares / last.equity
        facts.append(
            Fact(
                label=f"PBR ({last.year}년 자본 기준)",
                value=f"{pbr:.2f}배",
                key=sector_focus in ("pbr", "both"),
                hint="주가가 회사 순자산의 몇 배인지. 1배보다 낮으면 장부상 재산보다 싸게 거래되는 편이에요.",
            )
        )
        if len(past_pbr) >= 2:
            facts.append(_band("평소 PBR", pbr, past_pbr))
    return facts


def _band(label: str, now: float, past: list[float]) -> Fact:
    """이 회사의 평소 수준(지난 해들 연말 값)과 비교. 업종 평균이 아니라 '자기 자신'과 비교한다."""
    avg = sum(past) / len(past)
    where = "평소보다 낮은 편" if now < avg * 0.85 else "평소보다 높은 편" if now > avg * 1.15 else "평소와 비슷"
    return Fact(
        label=f"{label} {min(past):g}~{max(past):g}배",
        value=where,
        tone="",
        hint=f"지난 해들 연말 주가로 계산한 값의 범위예요(평균 {avg:.1f}배). 같은 회사의 평소 수준과 비교하면 지금이 비싼 편인지 싼 편인지 감이 와요.",
    )


def _growth_facts(years: list[YearRow], sector_focus: str) -> list[Fact]:
    facts: list[Fact] = []
    if len(years) < 2:
        return facts
    first, last = years[0], years[-1]
    if first.revenue and last.revenue and first.revenue > 0:
        n = last.year - first.year
        cagr = ((last.revenue / first.revenue) ** (1 / n) - 1) * 100 if n > 0 else 0
        facts.append(
            Fact(
                label=f"매출 성장 ({first.year}→{last.year})",
                value=f"연평균 {cagr:+.1f}%",
                tone=_tone(cagr),
                key=sector_focus == "per",
                hint="매출이 해마다 평균 몇 % 늘었는지예요. 이익을 보는 업종(PER)에서는 성장이 높은 PER을 설명해 줘요.",
            )
        )
    if last.op_margin is not None:
        trend = ""
        if first.op_margin is not None:
            if last.op_margin > first.op_margin + 1:
                trend = " (늘어나는 중)"
            elif last.op_margin < first.op_margin - 1:
                trend = " (줄어드는 중)"
        facts.append(
            Fact(
                label=f"영업이익률 ({last.year})",
                value=f"{last.op_margin:.1f}%{trend}",
                tone="down" if last.op_margin < 0 else "",
                hint="매출 100원 중 본업으로 남기는 돈이에요. 높고 늘어나는 중이면 장사를 잘하고 있다는 뜻이에요.",
            )
        )
    if last.roe is not None:
        facts.append(
            Fact(
                label=f"ROE ({last.year})",
                value=f"{last.roe:.1f}%",
                tone="down" if last.roe < 0 else "",
                key=sector_focus == "pbr",
                hint="자기 돈(자본)으로 1년에 몇 %를 벌었는지예요. 자산을 보는 업종(PBR)에서는 ROE가 높을수록 PBR도 높게 매겨져요.",
            )
        )
    return facts


# ── 업종 PER·PBR, 금리 (KRX) ─────────────────────────────

# KRX 업종 지수 (규모·우량 같은 묶음은 빼고 업종만). 종목이 여러 개에 속하면 가장 좁은 것을 쓴다.
SECTOR_INDEXES = (
    [str(c) for c in range(1005, 1027) if c not in (1022, 1023)]  # 코스피 음식료·담배(1005) ~ 일반서비스(1026)
    + ["2012", "2026", "2027", "2029", "2031", "2037", "2056", "2058", "2062", "2063", "2065", "2066",
       "2067", "2068", "2070", "2072", "2074", "2075", "2077", "2114", "2118"]  # 코스닥 업종
)
KRX_MARKET_INDEX = {"KOSPI": ("1001", "코스피"), "KOSDAQ": ("2001", "코스닥")}
SECTOR_REFRESH_MIN = 60 * 24 * 30  # 업종 구성은 한 달에 한 번
BONDS = (("국고채3년", "국고채 3년"), ("국고채10년", "국고채 10년"))
# 2026-11-25: KRX가 IP를 막아서 KRX는 ETF 구성종목 비중에만 쓰기로 했다. 타임머신은 KRX를 새로 부르지 않고
# 이미 저장해 둔 업종 PER·PBR·금리만 쓴다 (없는 날짜는 그 묶음이 숨겨진다). 다시 쓰려면 True로.
KRX_MARKET_DATA = False


def _ensure_sectors(db: Session) -> None:
    if not KRX_MARKET_DATA:
        return
    key, try_key = "krx-sectors", "krx-sectors-try"
    if fetch_log.is_fresh(db, key, SECTOR_REFRESH_MIN) or fetch_log.is_fresh(db, try_key, 60 * 6):
        return  # 한 달 안에 성공했거나, 6시간 안에 시도했다 실패했으면 넘어간다
    if krx.is_paused():
        return
    fetch_log.mark_fetched(db, try_key)
    db.commit()
    try:
        rows = []
        for code in SECTOR_INDEXES:
            members = client.fetch_index_members(code)
            if not members:
                continue
            name = client.fetch_index_name(code)
            rows += [SectorMember(index_code=code, stock_code=m, index_name=name, size=len(members)) for m in members]
        if rows:
            repository.replace_sector_members(db, rows)
        fetch_log.mark_fetched(db, key)
        db.commit()
    except Exception as e:  # KRX 로그인·사이트 문제면 업종 숫자만 빠진다
        db.rollback()
        print(f"  KRX 업종 구성 수집 실패: {e!r}")


HISTORY_START = date(2015, 1, 1)  # 업종 PER·PBR, 금리는 이날부터 오늘까지 한 번에 받아 둔다 (문제 날짜가 무작위라서)
RETRY_MIN = 30  # 받기에 실패하면 30분 동안은 다시 시도하지 않는다 (KRX는 로그인을 너무 자주 하면 잠깐 막는다)


def _covers(rows: list, start: date, end: date) -> bool:
    """[start, end] 구간이 빈 곳 없이 저장돼 있나. 거래일은 달력 날짜의 약 68%라 55%를 기준으로,
    끝(문제 날짜) 근처가 비어 있으면 옛날 값을 잘못 쓰게 되므로 마지막 값이 10일 안이어야 한다."""
    return len(rows) >= (end - start).days * 0.55 and rows[-1].date >= end - timedelta(days=10)


def _valuation_series(db: Session, index_code: str, start: date, end: date) -> list:
    rows = repository.find_index_valuation(db, index_code, start, end)
    if not _covers(rows, start, end) and _fetch_index_history(db, index_code):
        rows = repository.find_index_valuation(db, index_code, start, end)
    return rows if _covers(rows, start, end) or rows and rows[-1].date >= end - timedelta(days=10) else []


def _bond_series(db: Session, kind: str, start: date, end: date) -> list:
    rows = repository.find_bond_yields(db, kind, start, end)
    if not _covers(rows, start, end) and _fetch_bond_history(db, kind):
        rows = repository.find_bond_yields(db, kind, start, end)
    return rows if rows and rows[-1].date >= end - timedelta(days=10) else []


def _fetch_index_history(db: Session, index_code: str) -> bool:
    if not KRX_MARKET_DATA:
        return False
    key = f"krx-valuation-try:{index_code}"
    if krx.is_paused() or fetch_log.is_fresh(db, key, RETRY_MIN):
        return False
    fetch_log.mark_fetched(db, key)
    db.commit()
    try:
        fetched = client.fetch_index_valuation(index_code, HISTORY_START, date.today())
        repository.save_index_valuation(
            db,
            [IndexValuation(index_code=index_code, date=d, per=per, pbr=pbr, dividend_yield=dy) for d, per, pbr, dy in fetched],
        )
        db.commit()
        return bool(fetched)
    except Exception as e:
        db.rollback()
        print(f"  KRX 지수 PER·PBR 수집 실패({index_code}): {e!r}")
        return False


def _fetch_bond_history(db: Session, kind: str) -> bool:
    if not KRX_MARKET_DATA:
        return False
    key = f"krx-bond-try:{kind}"
    if krx.is_paused() or fetch_log.is_fresh(db, key, RETRY_MIN):
        return False
    fetch_log.mark_fetched(db, key)
    db.commit()
    try:
        fetched = client.fetch_bond_yields(kind, HISTORY_START, date.today())
        repository.save_bond_yields(db, [BondYield(kind=kind, date=d, value=v) for d, v in fetched])
        db.commit()
        return bool(fetched)
    except Exception as e:
        db.rollback()
        print(f"  국고채 금리 수집 실패({kind}): {e!r}")
        return False


def refresh_market_history(db: Session) -> int:
    """매일 수집(app.daily)용: 업종 구성, 코스피·코스닥·업종 지수 PER·PBR, 국고채 금리를 10년치 받아 둔다.
    문제를 낼 때 KRX에 묻지 않아도 되게 미리 채워 두는 것이다. 받은 지수·금리 개수를 돌려준다."""
    if not KRX_MARKET_DATA:
        return 0
    _ensure_sectors(db)
    count = 0
    for code in [c for c, _ in KRX_MARKET_INDEX.values()] + SECTOR_INDEXES:
        if krx.is_paused():  # 한 번 실패하면 나머지는 다음에 (KRX가 IP를 더 오래 막지 않게)
            return count
        if not fetch_log.is_fresh(db, f"krx-valuation-try:{code}", 60 * 12) and _fetch_index_history(db, code):
            count += 1
    for kind, _ in BONDS:
        if krx.is_paused():
            return count
        if not fetch_log.is_fresh(db, f"krx-bond-try:{kind}", 60 * 12) and _fetch_bond_history(db, kind):
            count += 1
    return count


def _compare(label: str, mine: float | None, theirs: float | None, unit_digits: int, key: bool) -> Fact | None:
    if not mine or not theirs:
        return None
    where = "업종보다 낮은 편" if mine < theirs * 0.85 else "업종보다 높은 편" if mine > theirs * 1.15 else "업종과 비슷"
    return Fact(
        label=label,
        value=f"{where} ({mine:.{unit_digits}f} vs {theirs:.{unit_digits}f})",
        key=key,
        hint="그날 이 종목 값과 같은 업종 회사들 전체 값을 비교했어요. 업종보다 낮다고 무조건 싼 건 아니에요(이익이 줄 거라 보는 경우도 있어요).",
    )


def _sector_facts(
    db: Session, code: str, market: str, as_of: date, stock_per: float | None, stock_pbr: float | None, sector_focus: str
) -> tuple[list[Fact], str | None]:
    """그날 KRX 업종 지수와 시장 전체의 PER·PBR. 업종 이름(KRX 기준)도 같이 돌려준다."""
    facts: list[Fact] = []
    _ensure_sectors(db)
    sec = repository.find_sector(db, code)
    sector_name = None
    if sec:
        sector_name = sec.index_name
        rows = [r for r in _valuation_series(db, sec.index_code, as_of - timedelta(days=365 * 3), as_of) if r.date <= as_of]
        now = rows[-1] if rows else None
        per_key, pbr_key = sector_focus in ("per", "both"), sector_focus in ("pbr", "both")
        if now and now.per:
            facts.append(
                Fact(
                    label=f"{sector_name} 업종 PER",
                    value=f"{now.per:.1f}배",
                    key=per_key,
                    hint="그날 이 업종에 속한 회사들 전체의 PER이에요(KRX 업종 지수 기준).",
                )
            )
            if c := _compare("이 종목 PER vs 업종", stock_per, now.per, 1, per_key):
                facts.append(c)
        if now and now.pbr:
            facts.append(
                Fact(
                    label=f"{sector_name} 업종 PBR",
                    value=f"{now.pbr:.2f}배",
                    key=pbr_key,
                    hint="그날 이 업종에 속한 회사들 전체의 PBR이에요(KRX 업종 지수 기준).",
                )
            )
            if c := _compare("이 종목 PBR vs 업종", stock_pbr, now.pbr, 2, pbr_key):
                facts.append(c)
        pers = [r.per for r in rows if r.per]
        if now and now.per and len(pers) >= 100:
            avg = sum(pers) / len(pers)
            where = "평소보다 싼 편" if now.per < avg * 0.85 else "평소보다 비싼 편" if now.per > avg * 1.15 else "평소와 비슷"
            facts.append(
                Fact(
                    label=f"업종 평소 PER {min(pers):.0f}~{max(pers):.0f}배 (3년)",
                    value=f"업종 전체가 {where}",
                    hint=f"지난 3년 동안 이 업종 PER의 범위예요(평균 {avg:.1f}배). 업종 전체가 비싸거나 싼 시기인지 볼 수 있어요.",
                )
            )
    m_code, m_name = KRX_MARKET_INDEX.get(market, KRX_MARKET_INDEX["KOSPI"])
    mrows = [r for r in _valuation_series(db, m_code, as_of - timedelta(days=45), as_of) if r.date <= as_of]
    if mrows and (mrows[-1].per or mrows[-1].pbr):
        m = mrows[-1]
        facts.append(
            Fact(
                label=f"{m_name} 전체 PER · PBR",
                value=f"{m.per or 0:.1f}배 · {m.pbr or 0:.2f}배",
                hint="그날 시장 전체 평균이에요. 업종·종목 값을 시장 평균과 견줘 볼 수 있어요.",
            )
        )
    return facts, sector_name


def _rate_facts(db: Session, as_of: date, highlight: bool) -> list[Fact]:
    """그날 국고채 금리와 1년 전 대비 변화. 금리는 주식 전체의 '가격표'에 영향을 준다."""
    facts: list[Fact] = []
    trend = None
    for kind, label in BONDS:
        rows = [r for r in _bond_series(db, kind, as_of - timedelta(days=400), as_of) if r.date <= as_of]
        if not rows:
            continue
        now = rows[-1].value
        ago_rows = [r for r in rows if r.date <= as_of - timedelta(days=365)]
        diff = now - ago_rows[-1].value if ago_rows else None
        value = f"{now:.2f}%" + (f" (1년 전보다 {diff:+.2f}%p)" if diff is not None else "")
        facts.append(
            Fact(
                label=f"{label} 금리",
                value=value,
                key=highlight,
                hint="나라가 돈을 빌릴 때 내는 이자예요. 다른 금리(예금·대출)의 기준이 돼요.",
            )
        )
        if kind == "국고채3년" and diff is not None:
            trend = diff
    if trend is not None:
        word = "오르는 중" if trend >= 0.25 else "내리는 중" if trend <= -0.25 else "큰 변화 없음"
        facts.append(
            Fact(
                label="금리 흐름 (1년)",
                value=word,
                key=highlight,
                hint="금리가 오르면 예금 매력이 커지고 회사 이자 부담이 늘어 주식 전체에 부담이 되는 경우가 많아요(특히 이익이 먼 미래에 있는 성장주). 은행은 반대로 이자 차이로 이익이 늘기도 해요.",
            )
        )
    return facts


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
