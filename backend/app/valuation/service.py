"""Service. Spring의 @Service에 해당한다.

PER·PBR을 직접 계산하고 같은 업종 회사들과 비교한다.
- PER = 주가 ÷ EPS(주당순이익)   → 회사가 1년에 버는 돈의 몇 배에 주가가 매겨졌나
- PBR = 주가 ÷ BPS(주당순자산)   → 회사가 가진 순자산의 몇 배에 주가가 매겨졌나
- 업종 기준: 네이버가 고른 같은 업종 주요 회사들(보통 5~6곳)의 PER·PBR 중간값.
  평균 대신 중간값을 쓰는 이유: 이익이 아주 적은 회사 하나가 PER 수백 배로 평균을 크게 흔들기 때문.
- 적자 회사(EPS가 0 이하)는 PER을 계산하지 않는다.
"""
import json
from datetime import date, datetime
from statistics import median

from sqlalchemy.orm import Session

from app.core import fetch_log
from app.stock import repository as stock_repository
from app.valuation import client, dart_client, focus, repository
from app.valuation.friendly import friendly
from app.valuation.models import AnnualFinancial, AnnualShares, CompanyOverview, Fundamental
from app.valuation.schemas import OverviewResponse, PeerValuation, ValuationResponse, YearValuation

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
    rule = focus.decide(me.industry_name, me.eps)

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
        focus=rule.focus,
        focus_title=rule.title,
        focus_reason=rule.reason,
        focus_also=list(rule.also),
        focus_caution=rule.caution,
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


def get_overview(db: Session, code: str) -> OverviewResponse:
    """회사 소개 + 연도별 PER·PBR 흐름. 네이버가 주는 최근 3개 연도 실적과 올해 증권사 예상치."""
    key = f"overview:{code}"
    if not fetch_log.is_fresh(db, key, REFRESH_MIN):
        try:
            summary, rows = client.fetch_overview(code)
            repository.save_overview(
                db,
                CompanyOverview(
                    stock_code=code,
                    summary="\n".join(summary),
                    annual_json=json.dumps(
                        [{"label": r.label, "is_estimate": r.is_estimate, "values": r.values} for r in rows],
                        ensure_ascii=False,
                    ),
                    fetched_at=datetime.now(),
                ),
            )
            fetch_log.mark_fetched(db, key)
            db.commit()
        except Exception as e:  # 네이버 장애로 화면 전체가 죽지 않게
            db.rollback()
            print(f"  회사 개요 수집 실패({code}): {e!r}")

    saved = repository.find_overview(db, code)
    if saved is None or (not saved.summary and saved.annual_json == "[]"):
        return OverviewResponse(available=False, message="회사 소개 정보가 없는 종목이에요. ETF는 회사가 아니라서 이 정보가 없어요.")

    years = [_to_year(r) for r in json.loads(saved.annual_json)]
    years = [y for y in years if any(v is not None for v in (y.per, y.pbr, y.eps, y.revenue))]
    # 네이버가 주지 않는 더 오래된 해는 공시(사업보고서)로 채운다 (최대 10년)
    naver_years = {y.label[:4] for y in years}
    years = [y for y in _dart_years(db, code) if y.label[:4] not in naver_years] + years
    me = repository.find(db, code)
    return OverviewResponse(
        available=True,
        # 네이버 보고서 말투("~하고 있음")를 해요체로. 빈 문장은 뺀다
        summary=[friendly(s) for s in saved.summary.split("\n") if s.strip(" .")],
        industry_name=me.industry_name if me else None,
        years=years,
        trend_comment=_trend_comment(years),
    )


def _to_year(row: dict) -> YearValuation:
    v = row["values"]
    eps, per = v.get("EPS"), v.get("PER")
    return YearValuation(
        label=row["label"],
        is_estimate=row["is_estimate"],
        per=per if per is not None and per > 0 and (eps is None or eps > 0) else None,  # 적자인 해는 PER 없음
        pbr=v.get("PBR"),
        eps=eps,
        bps=v.get("BPS"),
        revenue=v.get("매출액"),
        operating_profit=v.get("영업이익"),
        roe=v.get("ROE"),
        dividend=v.get("주당배당금"),
    )


def _trend_comment(years: list[YearValuation]) -> str | None:
    """실제 실적이 나온 해들만 보고 흐름을 말한다 (예상치는 따로 언급)."""
    actual = [y for y in years if not y.is_estimate]
    if len(actual) < 2:
        return None
    parts = []
    first, last = actual[0], actual[-1]
    if first.operating_profit and last.operating_profit and first.operating_profit > 0:
        change = (last.operating_profit / first.operating_profit - 1) * 100
        word = "늘었어요" if change > 5 else "줄었어요" if change < -5 else "비슷해요"
        if change >= 100:  # "564% 늘었어요"보다 "약 6.6배가 됐어요"가 읽기 쉽다
            parts.append(f"영업이익은 {first.label[:4]}년에 비해 {last.label[:4]}년에 약 {change / 100 + 1:.1f}배가 됐어요.")
        else:
            parts.append(f"영업이익은 {first.label[:4]}년에 비해 {last.label[:4]}년에 {abs(change):.0f}% {word}." if word != "비슷해요"
                     else f"영업이익은 {first.label[:4]}년과 {last.label[:4]}년이 비슷해요.")
    loss_years = [y.label[:4] for y in actual if y.eps is not None and y.eps <= 0]
    if loss_years:
        parts.append(f"{', '.join(loss_years)}년은 주주 몫 순이익이 적자라 PER이 없어요.")
    if first.pbr and last.pbr:
        if last.pbr > first.pbr * 1.3:
            parts.append(f"PBR은 {first.pbr:g}배에서 {last.pbr:g}배로 올랐어요. 자산에 비해 주가가 더 높게 매겨졌다는 뜻이에요.")
        elif last.pbr < first.pbr * 0.7:
            parts.append(f"PBR은 {first.pbr:g}배에서 {last.pbr:g}배로 내렸어요.")
    est = next((y for y in years if y.is_estimate and y.per), None)
    if est:
        parts.append(f"증권사들은 {est.label[:4]}년 이익 기준 PER을 {est.per:g}배로 예상해요.")
    return " ".join(parts) or None


DART_YEARS = 10
DART_REFRESH_MIN = 60 * 24 * 7  # 새 사업보고서는 1년에 한 번 나오므로 일주일에 한 번만 확인


def _dart_years(db: Session, code: str) -> list[YearValuation]:
    """OpenDART 사업보고서로 지난 10년 PER·PBR을 만든다.

    - 그해 마지막 거래일 종가 ÷ (당기순이익 ÷ 그해 주식 수) = PER,  종가 ÷ (자본총계 ÷ 그해 주식 수) = PBR
    - 해마다 그해 말 주식 수를 쓰므로 자사주 소각·증자도 반영된다 (2026-11-17, 예전엔 최근 주식 수 하나로 계산)
    - 주가는 액면분할을 반영한 값이라, 분할 전 해의 주식 수는 분할 비율만큼 곱해 같은 기준으로 맞춘다 (_split_adjusted)
    - 당기순이익은 비지배주주 몫이 포함돼 네이버(지배주주 기준) 숫자와 조금 다르다
    """
    from app.disclosure import repository as disclosure_repository  # 종목코드 → DART 회사번호
    from app.stock import repository as stock_repository

    corp = disclosure_repository.find_corp(db, code)
    if corp is None:
        return []
    key = f"dart-annual:{code}"
    if not fetch_log.is_fresh(db, key, DART_REFRESH_MIN):
        try:
            have = {a.year for a in repository.find_annual(db, code)}
            this_year = date.today().year
            for year in range(this_year - DART_YEARS, this_year):
                if year in have:
                    continue
                acc = dart_client.fetch_annual(corp.corp_code, year)
                if acc:
                    repository.save_annual(
                        db,
                        AnnualFinancial(
                            stock_code=code, year=year, revenue=acc.revenue, operating_profit=acc.operating_profit,
                            net_income=acc.net_income, equity=acc.equity,
                        ),
                    )
            fetch_log.mark_fetched(db, key)
            db.commit()
        except Exception as e:  # 키가 없거나 OpenDART 장애면 네이버 숫자만 보여준다
            db.rollback()
            print(f"  공시 재무 수집 실패({code}): {e!r}")

    rows = repository.find_annual(db, code)
    if not rows:
        return []
    _collect_shares(db, code, corp.corp_code, [a.year for a in rows])
    shares_by_year = _split_adjusted(repository.find_shares(db, code))
    if not shares_by_year:
        return []
    out = []
    for a in rows:
        shares = shares_by_year.get(a.year)
        if not shares:
            continue
        close = _year_end_close(stock_repository, db, code, a.year)
        eps = a.net_income / shares if a.net_income is not None else None
        bps = a.equity / shares if a.equity is not None else None
        out.append(
            YearValuation(
                label=f"{a.year}.12",
                is_estimate=False,
                per=round(close / eps, 2) if close and eps and eps > 0 else None,
                pbr=round(close / bps, 2) if close and bps and bps > 0 else None,
                eps=round(eps) if eps is not None else None,
                bps=round(bps) if bps is not None else None,
                revenue=round(a.revenue / 1e8) if a.revenue is not None else None,  # 억원 (네이버와 같은 단위)
                operating_profit=round(a.operating_profit / 1e8) if a.operating_profit is not None else None,
                roe=round(a.net_income / a.equity * 100, 2) if a.net_income is not None and a.equity else None,
                dividend=None,
                source="dart",
            )
        )
    return out


def _collect_shares(db: Session, code: str, corp_code: str, years: list[int]) -> None:
    """아직 없는 해의 주식 수를 받는다. 지난 해 숫자는 바뀌지 않으므로 한 번 받으면 끝."""
    key = f"dart-shares:{code}"
    if fetch_log.is_fresh(db, key, DART_REFRESH_MIN):
        return
    try:
        have = repository.find_shares(db, code)
        for year in years:
            if year in have:
                continue
            n = dart_client.fetch_shares(corp_code, year)
            if n:
                repository.save_shares(db, AnnualShares(stock_code=code, year=year, shares=n))
        fetch_log.mark_fetched(db, key)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"  주식 수 수집 실패({code}): {e!r}")


SPLIT_RATIOS = (2, 4, 5, 10, 20, 25, 50, 100)  # 흔한 액면분할 비율


def _split_adjusted(shares: dict[int, int]) -> dict[int, float]:
    """액면분할 전 해의 주식 수를 지금 기준으로 맞춘다.

    주가 데이터는 분할을 반영해 과거 가격을 낮춰 둔 값이라, 주식 수도 분할 비율만큼 늘려야 1주당 이익이 맞는다.
    한 해 사이 주식 수가 흔한 분할 비율(2·5·10·50배 등)에 가깝게(±3%) 늘었으면 분할로 본다.
    예: 삼성전자 2017년 약 1.29억 주 → 2018년 약 64억 주 (50:1 분할) → 2017년 이전은 ×50
    """
    years = sorted(shares)
    out: dict[int, float] = {}
    factor = 1.0
    for i in range(len(years) - 1, -1, -1):
        y = years[i]
        out[y] = shares[y] * factor
        if i > 0:
            prev = years[i - 1]
            ratio = shares[y] / shares[prev] if shares[prev] else 1
            split = next((r for r in SPLIT_RATIOS if abs(ratio - r) / r < 0.03), None)
            if split:
                factor *= split
    return out


def _year_end_close(stock_repository, db: Session, code: str, year: int) -> int | None:
    prices = stock_repository.find_prices(db, code, date(year, 12, 1))
    in_year = [p for p in prices if p.date.year == year]
    return in_year[-1].close if in_year else None
