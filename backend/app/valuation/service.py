"""Service. Spring의 @Service에 해당한다.

PER·PBR을 직접 계산하고 같은 업종 회사들과 비교한다.
- PER = 주가 ÷ EPS(주당순이익)   → 회사가 1년에 버는 돈의 몇 배에 주가가 매겨졌나
- PBR = 주가 ÷ BPS(주당순자산)   → 회사가 가진 순자산의 몇 배에 주가가 매겨졌나
- 업종 기준: 네이버가 고른 같은 업종 주요 회사들(보통 5~6곳)의 PER·PBR 중간값.
  평균 대신 중간값을 쓰는 이유: 이익이 아주 적은 회사 하나가 PER 수백 배로 평균을 크게 흔들기 때문.
- 적자 회사(EPS가 0 이하)는 PER을 계산하지 않는다.
"""
from datetime import datetime
from statistics import median

from sqlalchemy.orm import Session

from app.core import fetch_log
from app.stock import repository as stock_repository
from app.valuation import client, repository
from app.valuation.models import Fundamental
from app.valuation.schemas import PeerValuation, ValuationResponse

REFRESH_MIN = 720  # 재무 숫자는 분기마다 바뀌므로 반나절에 한 번이면 충분하다
SIMILAR_PCT = 15  # 업종과 ±15% 안이면 "비슷해요"


def get_by_stock(db: Session, code: str) -> ValuationResponse:
    me = _refresh(db, code)
    if me is None or (me.eps is None and me.bps is None):
        return ValuationResponse(available=False, message="PER·PBR 정보가 없는 종목이에요. ETF는 회사가 아니라서 이 지표가 없어요.")

    # 우리 DB의 최근 종가로 직접 계산한다. 없으면 네이버가 쓴 주가로.
    latest = stock_repository.find_recent_prices(db, code, 1)
    price, price_date = (latest[0].close, latest[0].date) if latest else (me.price, None)

    per = round(price / me.eps, 2) if price and me.eps and me.eps > 0 else None
    pbr = round(price / me.bps, 2) if price and me.bps and me.bps > 0 else None

    peer_codes = [c for c in me.peer_codes.split(",") if c]
    for c in peer_codes:
        _refresh(db, c)
    peers = repository.find_many(db, peer_codes)
    peers.sort(key=lambda p: peer_codes.index(p.stock_code))

    industry_per = _median([p.per for p in peers])
    industry_pbr = _median([p.pbr for p in peers])
    per_gap = _gap(per, industry_per)
    pbr_gap = _gap(pbr, industry_pbr)

    return ValuationResponse(
        available=True,
        price=price,
        price_date=price_date,
        eps=me.eps,
        bps=me.bps,
        per=per,
        pbr=pbr,
        cns_per=me.cns_per,
        industry_name=me.industry_name,
        industry_per=industry_per,
        industry_pbr=industry_pbr,
        per_gap_pct=per_gap,
        pbr_gap_pct=pbr_gap,
        per_comment=_per_comment(me.eps, per, per_gap),
        pbr_comment=_comment(pbr_gap, "순자산"),
        peers=[PeerValuation(code=p.stock_code, name=p.name, per=p.per, pbr=p.pbr) for p in peers],
    )


def _refresh(db: Session, code: str) -> Fundamental | None:
    """반나절 안에 받은 적이 없으면 네이버에서 다시 받아 저장한다. 실패하면 저장된 것을 쓴다."""
    key = f"fundamental:{code}"
    if not fetch_log.is_fresh(db, key, REFRESH_MIN):
        try:
            row = client.fetch_fundamental(code)
            industry_name = None
            if row.industry_code:
                industry_name = repository.find_industry_name(db, row.industry_code) or client.fetch_industry_name(
                    row.industry_code
                )
            repository.save(
                db,
                Fundamental(
                    stock_code=code,
                    name=row.name,
                    price=row.price,
                    eps=row.eps,
                    bps=row.bps,
                    per=row.per,
                    pbr=row.pbr,
                    cns_per=row.cns_per,
                    industry_code=row.industry_code,
                    industry_name=industry_name,
                    peer_codes=",".join(row.peer_codes),
                    fetched_at=datetime.now(),
                ),
            )
            fetch_log.mark_fetched(db, key)
            db.commit()
        except Exception as e:  # 네이버 장애로 화면 전체가 죽지 않게
            db.rollback()
            print(f"  지표 수집 실패({code}): {e!r}")
    return repository.find(db, code)


def _median(values: list[float | None]) -> float | None:
    """0 이하(적자)는 빼고 중간값. 비교할 회사가 2곳 미만이면 기준으로 쓰지 않는다."""
    ok = [v for v in values if v is not None and v > 0]
    return round(median(ok), 2) if len(ok) >= 2 else None


def _gap(mine: float | None, industry: float | None) -> float | None:
    if mine is None or industry is None:
        return None
    return round((mine / industry - 1) * 100, 1)


def _comment(gap: float | None, base: str) -> str | None:
    if gap is None:
        return None
    if abs(gap) < SIMILAR_PCT:
        return f"업종과 비슷한 수준이에요. {base}에 비해 주가가 업종 평균만큼 매겨져 있어요."
    if gap < 0:
        return f"업종보다 {abs(gap):.0f}% 낮아요. {base}에 비해 주가가 낮게 매겨진 편이에요."
    if gap >= 100:  # "+4559%"보다 "약 46배"가 읽기 쉽다
        return f"업종의 약 {gap / 100 + 1:.1f}배예요. {base}에 비해 주가가 높게 매겨진 편이에요."
    return f"업종보다 {gap:.0f}% 높아요. {base}에 비해 주가가 높게 매겨진 편이에요."


HUGE_PER = 100  # 이보다 크면 이익이 아주 적어서 PER이 부풀려진 경우가 많다


def _per_comment(eps: float | None, per: float | None, gap: float | None) -> str | None:
    if eps is not None and eps <= 0:
        return "최근 1년 적자라 PER을 계산할 수 없어요."
    text = _comment(gap, "이익")
    if per is not None and per >= HUGE_PER:
        note = "최근 1년 이익이 아주 적어서 PER이 크게 나와요. 이럴 땐 PER보다 PBR과 실적 흐름을 함께 보세요."
        return f"{text} {note}" if text else note
    return text
