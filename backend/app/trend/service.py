"""Service. Spring의 @Service에 해당한다.

투자자별 매매동향을 받아 쌓고, 최근 5·20·60거래일 합계와 한 줄 설명을 만든다.
- 6시간에 한 번 최근 60거래일을 다시 받는다 (장 마감 뒤 값이 확정되므로 덮어쓴다)
- 처음 보는 종목은 한 번 더 과거 60일을 받아 약 6개월을 채운다
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core import fetch_log
from app.trend import client, repository
from app.trend.models import InvestorTrend
from app.trend.schemas import TrendDay, TrendResponse, TrendSummary

REFRESH_MIN = 360
SUM_DAYS = (5, 20, 60)


def get_by_stock(db: Session, code: str, days: int) -> TrendResponse:
    _refresh(db, code)
    rows = repository.find_since(db, code, date.today() - timedelta(days=days))
    if not rows:
        return TrendResponse(available=False, message="매매동향 정보가 없어요. ETF나 거래가 적은 종목은 없을 수 있어요.")
    items = [TrendDay(date=r.date, foreign=r.foreign, organ=r.organ, individual=r.individual, foreign_ratio=r.foreign_ratio) for r in rows]
    summary = [
        TrendSummary(
            days=len(recent),
            foreign=sum(r.foreign for r in recent),
            organ=sum(r.organ for r in recent),
            individual=sum(r.individual for r in recent),
        )
        for n in SUM_DAYS
        if (recent := items[-n:]) and len(items) >= min(n, len(items))
    ]
    return TrendResponse(available=True, items=items, summary=summary, comment=_comment(items))


def _refresh(db: Session, code: str) -> None:
    key = f"trend:{code}"
    if fetch_log.is_fresh(db, key, REFRESH_MIN):
        return
    try:
        first_time = repository.find_earliest_date(db, code) is None
        rows = client.fetch_trend(code)
        if first_time and rows:
            rows += client.fetch_trend(code, before=min(r.date for r in rows))
        repository.save_all(
            db,
            [
                InvestorTrend(
                    stock_code=code, date=r.date, foreign=r.foreign, organ=r.organ, individual=r.individual, foreign_ratio=r.foreign_ratio
                )
                for r in rows
            ],
        )
        fetch_log.mark_fetched(db, key)
        db.commit()
    except Exception as e:  # 네이버 장애로 화면 전체가 죽지 않게
        db.rollback()
        print(f"  매매동향 수집 실패({code}): {e!r}")


def _streak(values: list[int]) -> int:
    """마지막 날부터 같은 방향(순매수/순매도)이 며칠 이어졌는지. 순매수면 +, 순매도면 -."""
    if not values or values[-1] == 0:
        return 0
    sign = 1 if values[-1] > 0 else -1
    n = 0
    for v in reversed(values):
        if v * sign > 0:
            n += 1
        else:
            break
    return n * sign


def _comment(items: list[TrendDay]) -> str | None:
    parts = []
    for name, vals in (("외국인", [i.foreign for i in items]), ("기관", [i.organ for i in items])):
        s = _streak(vals)
        if abs(s) >= 3:
            parts.append(f"{name}이 {abs(s)}거래일 연속 {'사고' if s > 0 else '팔고'} 있어요.")
    if len(items) >= 20:
        f20 = sum(i.foreign for i in items[-20:])
        o20 = sum(i.organ for i in items[-20:])
        both = "사들였어요" if f20 > 0 and o20 > 0 else "팔았어요" if f20 < 0 and o20 < 0 else None
        if both:
            parts.append(f"최근 20거래일 동안 외국인과 기관이 함께 {both}.")
    return " ".join(parts) or None
