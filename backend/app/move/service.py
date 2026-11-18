"""Service. Spring의 @Service에 해당한다.

"오늘 왜 움직였지?": 종목이 크게 오르내린 날을 찾아, 같은 날 있었던 일을 모은다.
- 크게 움직인 날: 둘 중 하나라도 기준을 넘은 날. 기준은 종목마다 다르다 (평소 변동폭의 2.5배, 최소 4%)
  1) 전 거래일 대비 등락률 — 삼성전자의 5%와 작은 회사의 5%는 무게가 달라서 종목마다 기준을 둔다
  2) 시장 지수보다 더(덜) 움직인 폭 — 시장이 크게 흔들리는 시기엔 1)이 시장 전체의 날만 고르게 되므로,
     이 종목만의 일이 있었던 날을 따로 잡는다
- 같은 날 시장 지수(코스피·코스닥): 시장 전체가 같이 움직였는지, 이 종목만 움직였는지
- 공시: 그날과 전 거래일(장 마감 뒤 공시는 다음 날 주가에 반영되는 경우가 많다)
- 투자자별 순매수: 그날 외국인·기관·개인 (최근 몇 달 것만 있음)
뉴스·리포트는 화면이 이미 날짜별로 가지고 있어서 여기서는 다루지 않는다.

원인을 단정하지 않는다. "같은 날 있었던 일"로만 보여준다.
"""
import statistics
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core import fetch_log
from app.disclosure import keypoints
from app.disclosure import repository as disclosure_repository
from app.move import client, repository
from app.move.models import IndexPrice
from app.move.schemas import BigMove, MoveDisclosure, MovesResponse, MoveTrend
from app.stock import repository as stock_repository
from app.trend import repository as trend_repository

INDEX = {"KOSPI": ("KS11", "코스피"), "KOSDAQ": ("KQ11", "코스닥")}
INDEX_REFRESH_MIN = 720
INDEX_YEARS = 10
MIN_THRESHOLD = 4.0  # %
STD_MULTIPLE = 2.5
MAX_THRESHOLD = 15.0
MAX_MOVES = 40
VOLUME_DAYS = 20


def get_moves(db: Session, code: str, days: int) -> MovesResponse:
    stock = stock_repository.find_stock(db, code)
    if stock is None:
        return MovesResponse(available=False, message="종목을 찾을 수 없어요.")
    start = date.today() - timedelta(days=days)
    prices = stock_repository.find_prices(db, code, start - timedelta(days=60))  # 거래량 평균용으로 조금 더
    if len(prices) < 30:
        return MovesResponse(available=False, message="주가 데이터가 부족해요.")

    index_code, index_name = INDEX.get(stock.market, INDEX["KOSPI"])
    _refresh_index(db, index_code)
    index_close = {p.date: p.close for p in repository.find_since(db, index_code, start - timedelta(days=90))}
    index_dates = sorted(index_close)

    returns = [(b.close / a.close - 1) * 100 for a, b in zip(prices, prices[1:]) if a.close]
    std = statistics.pstdev(returns)
    threshold = _threshold(std)
    excess = [
        (b.close / a.close - 1) * 100 - x
        for a, b in zip(prices, prices[1:])
        if a.close and (x := _index_change(index_close, index_dates, b.date)) is not None
    ]
    excess_std = statistics.pstdev(excess) if len(excess) > 20 else None
    excess_threshold = _threshold(excess_std) if excess_std else None

    moves: list[BigMove] = []
    for i in range(1, len(prices)):
        day, prev = prices[i], prices[i - 1]
        if day.date < start or not prev.close:
            continue
        pct = (day.close / prev.close - 1) * 100
        idx_pct = _index_change(index_close, index_dates, day.date)
        alone = excess_threshold is not None and idx_pct is not None and abs(pct - idx_pct) >= excess_threshold
        if abs(pct) < threshold and not alone:
            continue
        recent_vol = [p.volume for p in prices[max(0, i - VOLUME_DAYS) : i] if p.volume]
        vol_ratio = round(day.volume / (sum(recent_vol) / len(recent_vol)), 1) if recent_vol and day.volume else None
        scope, scope_text = _scope(pct, idx_pct, index_name, alone)
        trend, trend_text = _trend(db, code, day.date)
        moves.append(
            BigMove(
                date=day.date,
                change_pct=round(pct, 2),
                volume_ratio=vol_ratio,
                index_name=index_name,
                index_change_pct=None if idx_pct is None else round(idx_pct, 2),
                scope=scope,
                scope_text=scope_text,
                disclosures=_disclosures(db, code, prev.date, day.date),
                trend=trend,
                trend_text=trend_text,
            )
        )
    moves.sort(key=lambda m: m.date, reverse=True)
    return MovesResponse(
        available=True,
        threshold_pct=threshold,
        threshold_text=f"이 종목은 평소 하루에 ±{std:.1f}% 정도 움직여요. ±{threshold:g}% 넘게 움직인 날"
        + (f"과, {index_name}보다 {excess_threshold:g}%p 넘게 더 움직인 날" if excess_threshold else "")
        + "을 골랐어요.",
        moves=moves[:MAX_MOVES],
    )


def _threshold(std: float) -> float:
    return min(max(MIN_THRESHOLD, round(std * STD_MULTIPLE * 2) / 2), MAX_THRESHOLD)


def _josa(word: str, with_final: str, without_final: str) -> str:
    """받침이 있으면 앞의 조사, 없으면 뒤의 조사 (코스닥은 / 코스피는)."""
    last = word[-1]
    has_final = "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 != 0
    return word + (with_final if has_final else without_final)


def _refresh_index(db: Session, index_code: str) -> None:
    key = f"index:{index_code}"
    if fetch_log.is_fresh(db, key, INDEX_REFRESH_MIN):
        return
    try:
        latest = repository.find_latest_date(db, index_code)
        start = latest - timedelta(days=7) if latest else date.today() - timedelta(days=365 * INDEX_YEARS + 10)
        rows = client.fetch_index(index_code, start)
        repository.save_all(db, [IndexPrice(index_code=index_code, date=d, close=c) for d, c in rows])
        fetch_log.mark_fetched(db, key)
        db.commit()
    except Exception as e:  # 지수를 못 받아도 나머지는 보여준다
        db.rollback()
        print(f"  지수 수집 실패({index_code}): {e!r}")


def _index_change(index_close: dict, index_dates: list, d: date) -> float | None:
    if d not in index_close:
        return None
    i = index_dates.index(d)
    if i == 0:
        return None
    before = index_close[index_dates[i - 1]]
    return (index_close[d] / before - 1) * 100 if before else None


def _scope(pct: float, idx_pct: float | None, index_name: str, alone: bool) -> tuple[str, str]:
    if idx_pct is None:
        return "unknown", f"이날 {index_name} 지수 정보가 없어요."
    idx_pct = idx_pct + 0.0 if abs(idx_pct) >= 0.05 else 0.0  # "-0.0%" 방지
    same_way = (pct > 0) == (idx_pct > 0)
    if same_way and abs(idx_pct) >= 1.5 and abs(idx_pct) >= abs(pct) * 0.3:
        if alone:
            word = "올랐" if pct > 0 else "빠졌"
            return "both", (
                f"이날 {index_name}도 {idx_pct:+.1f}% 움직였지만, 이 종목은 그보다 훨씬 더 {word}어요. "
                "시장 분위기에 이 종목만의 일이 겹쳤을 수 있어요."
            )
        return "market", (
            f"이날 {index_name}도 {idx_pct:+.1f}% 움직였어요. 시장 전체가 크게 흔들린 날이라 이 종목만의 일은 아닐 수 있어요."
        )
    return "stock", (
        f"이날 {_josa(index_name, '은', '는')} {idx_pct:+.1f}%였어요. 시장보다 이 종목이 훨씬 크게 움직여서, 이 종목에 무슨 일이 있었을 가능성이 커요."
    )


def _disclosures(db: Session, code: str, prev_day: date, day: date) -> list[MoveDisclosure]:
    rows = [d for d in disclosure_repository.find_by_stock(db, code, prev_day) if d.rcept_dt <= day]
    out = []
    for d in rows:
        rule = keypoints.classify(d.report_nm)
        if rule.level == "info":  # 정기 보고서·지분 보고 같은 참고용은 빼고
            continue
        out.append(
            MoveDisclosure(
                date=d.rcept_dt,
                title=d.report_nm,
                category=rule.category,
                level=rule.level,
                url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d.rcept_no}",
                timing="이날" if d.rcept_dt == day else "전 거래일 장 마감 후~휴일",
            )
        )
    return out


def _trend(db: Session, code: str, day: date) -> tuple[MoveTrend | None, str | None]:
    row = next((t for t in trend_repository.find_since(db, code, day) if t.date == day), None)
    if row is None:
        return None, None
    names = {"외국인": row.foreign, "기관": row.organ, "개인": row.individual}
    buyer = max(names, key=names.get)
    seller = min(names, key=names.get)
    text = f"이날 가장 많이 산 쪽은 {buyer}, 가장 많이 판 쪽은 {_josa(seller, '이었어요', '였어요')}."
    return MoveTrend(foreign=row.foreign, organ=row.organ, individual=row.individual), text
