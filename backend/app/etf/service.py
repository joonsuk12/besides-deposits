"""Service. Spring의 @Service에 해당한다.

ETF 정보를 반나절에 한 번 받아 저장하고, 화면용으로 정리한다.
- 영어 코드(EQUITY, IT …)를 한글로 바꾸고, 비중 0%인 항목은 뺀다
- 금 같은 원자재 ETF는 담긴 "종목" 대신 "설정현금액 100%"처럼 나와서, 실제 자산(금 현물 등)만 남긴다
- 보수·괴리율·추적오차를 보고 초보용 한 줄 해설을 붙인다 (매수·매도 권유는 하지 않는다)
"""
import json
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.core import fetch_log
from app.etf import client, repository
from app.etf.models import EtfInfo
from app.etf.schemas import EtfResponse, LabeledValue, Weight

REFRESH_MIN = 720

ASSET_NAMES = {"EQUITY": "주식", "BOND": "채권", "CASH": "현금", "OTHERS": "기타(원자재 등)", "DERIVATIVES": "파생상품"}
SECTOR_NAMES = {
    "IT": "IT", "INDUSTRIALS": "산업재", "FINANCIALS": "금융", "CONSUMER_DISCRETIONARY": "경기소비재",
    "CONSUMER_STAPLES": "필수소비재", "COMMUNICATION": "커뮤니케이션", "HEALTHCARE": "헬스케어", "MATERIALS": "소재",
    "ENERGY": "에너지", "UTILITIES": "유틸리티", "REAL_ESTATE": "부동산", "UNCLASSIFIED": "분류 안 됨",
}
PERIODS = {"M1": "1개월", "M3": "3개월", "M6": "6개월", "YTD": "올해", "Y1": "1년", "Y3": "3년"}
INFLOWS = [("cumulativeNetInflow1m", "1개월"), ("cumulativeNetInflow3m", "3개월"), ("cumulativeNetInflow1y", "1년")]
# 담긴 종목 목록에 섞여 나오는 현금성 항목 (실제로 무엇에 투자하는지 보여주려고 뺀다)
CASH_LIKE = ("설정현금액", "원화현금", "현금", "예금")


def get_by_stock(db: Session, code: str) -> EtfResponse:
    key = f"etf:{code}"
    if not fetch_log.is_fresh(db, key, REFRESH_MIN):
        try:
            d = client.fetch_etf(code)
            if d:
                repository.save(db, EtfInfo(stock_code=code, raw_json=json.dumps(d, ensure_ascii=False), fetched_at=datetime.now()))
            fetch_log.mark_fetched(db, key)
            db.commit()
        except Exception as e:  # 네이버 장애로 화면 전체가 죽지 않게
            db.rollback()
            print(f"  ETF 정보 수집 실패({code}): {e!r}")

    saved = repository.find(db, code)
    if saved is None:
        return EtfResponse(available=False, message="ETF 정보가 없어요.")
    return _to_response(json.loads(saved.raw_json))


def _weights(rows: list[dict] | None, names: dict[str, str]) -> list[Weight]:
    out = [Weight(name=names.get(r.get("detailTypeCode", ""), r.get("detailTypeCode", "")), weight=r.get("weight") or 0) for r in rows or []]
    return sorted([w for w in out if w.weight >= 0.1], key=lambda w: -w.weight)


def _pct(text: str | None) -> float | None:
    try:
        return float((text or "").replace("%", "").replace(",", ""))
    except ValueError:
        return None


def _to_response(d: dict) -> EtfResponse:
    holdings = []
    for r in sorted(d.get("etfTop10MajorConstituentAssets") or [], key=lambda r: r.get("seq", 0)):
        name = r.get("itemName") or ""
        if any(c in name for c in CASH_LIKE):
            continue
        holdings.append(Weight(name=name, weight=_pct(r.get("etfWeight")) or 0, code=r.get("itemCode") or None))

    sectors = _weights(d.get("sectorPortfolioList"), SECTOR_NAMES)
    if len(sectors) == 1 and sectors[0].name == "분류 안 됨":
        sectors = []  # 금·채권 ETF처럼 업종이 의미 없는 경우

    dev = d.get("deviationRate")
    if dev is not None and d.get("deviationSign") == "-":
        dev = -dev
    listed = d.get("listedDate") or ""
    dividend = d.get("dividend") or {}
    inflow = d.get("cumulativeNetInflowList") or {}

    res = EtfResponse(
        available=True,
        name=d.get("itemName"),
        base_index=d.get("etfBaseIndex"),
        issuer=(d.get("issuerName") or "").replace("(ETF)", "").strip() or None,
        listed_date=f"{listed[:4]}-{listed[4:6]}-{listed[6:8]}" if len(listed) == 8 else None,
        summary=_first_sentences(d.get("etfSummary")),
        total_fee=d.get("totalFee"),
        deviation_rate=dev,
        tracking_error=d.get("chaseErrorRate"),
        total_nav=d.get("totalNav"),
        returns=[
            LabeledValue(label=PERIODS[r["periodTypeCode"]], value=r.get("value"))
            for r in d.get("returnPerformanceList") or []
            if r.get("periodTypeCode") in PERIODS
        ],
        holdings=_fill_single_weight(holdings, _weights(d.get("assetPortfolioList"), ASSET_NAMES)),
        assets=_weights(d.get("assetPortfolioList"), ASSET_NAMES),
        sectors=sectors,
        dividend_yield=dividend.get("dividendYieldTtm") or None,
        dividend_months=_months(dividend.get("dividendMonthThisYear")),
        inflows=[LabeledValue(label=label, value=inflow.get(k)) for k, label in INFLOWS if inflow.get(k) not in (None, "-")],
    )
    res.notes = _notes(res)
    return res


def _fill_single_weight(holdings: list[Weight], assets: list[Weight]) -> list[Weight]:
    """금 ETF처럼 실제 자산이 하나뿐인데 네이버가 비중을 "-"로 줄 때, 현금을 뺀 자산 비중으로 채운다.

    예: ACE KRX금현물 — 담긴 것 "금 현물 99.99_1Kg" 비중 "-", 자산 구성 "기타(원자재 등) 99.94%" → 금 현물 99.94%
    """
    if len(holdings) == 1 and holdings[0].weight == 0:
        non_cash = [a for a in assets if a.name != "현금"]
        if non_cash:
            holdings[0].weight = non_cash[0].weight
    return holdings


def _first_sentences(text: str | None, n: int = 2) -> str | None:
    if not text:
        return None
    text = re.sub(r"<[^>]+>", " ", text).replace("·", "")  # 운용사가 쓴 <br> 같은 태그 빼기
    parts = [p.strip() for p in text.replace("다.", "다.\n").split("\n") if p.strip()]
    return " ".join(parts[:n])


def _months(text: str | None) -> str | None:
    if not text:
        return None
    return ", ".join(f"{m.strip()}월" for m in text.split(",") if m.strip())


def _notes(r: EtfResponse) -> list[str]:
    """초보용 한 줄 해설. 좋다·나쁘다가 아니라 숫자를 어떻게 읽는지 알려준다."""
    notes = []
    if r.total_fee is not None:
        level = "낮은 편" if r.total_fee <= 0.2 else "보통" if r.total_fee <= 0.5 else "높은 편"
        notes.append(f"총보수 연 {r.total_fee}%는 ETF 중 {level}이에요. 오래 가지고 있을수록 보수 차이가 쌓여요.")
    if r.deviation_rate is not None:
        if abs(r.deviation_rate) < 0.5:
            notes.append(f"괴리율 {r.deviation_rate:+.2f}%: 실제 담긴 자산 가치(NAV)와 거의 같은 값에 거래되고 있어요.")
        else:
            side = "비싸게" if r.deviation_rate > 0 else "싸게"
            notes.append(f"괴리율 {r.deviation_rate:+.2f}%: 담긴 자산 가치보다 {side} 거래되고 있어요. 1% 넘게 벌어지면 주의해서 보세요.")
    if r.tracking_error is not None:
        level = "잘 따라가고" if r.tracking_error < 1 else "조금 벗어나고"
        notes.append(f"추적오차 {r.tracking_error}%: 따라가는 지수를 {level} 있어요. 작을수록 지수와 비슷하게 움직여요.")
    return notes
