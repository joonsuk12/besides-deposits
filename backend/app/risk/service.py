"""Service. Spring의 @Service에 해당한다.

초보가 놓치기 쉬운 위험 신호를 종목마다 신호등(초록·노랑·빨강)으로 정리한다.
새로 외부에서 받는 데이터는 없고, 이미 모아 둔 것을 다시 읽는다.
- 최근 1년 공시 (disclosure 도메인: 공시 이름 규칙으로 분류한 결과를 그대로 쓴다)
- 연도별 순이익·자본총계 (valuation 도메인: OpenDART 사업보고서)

"좋은 종목"을 고르는 게 아니라 "확인해야 할 함정"을 보여준다. 매수·매도 권유는 하지 않는다.
문제가 없는 항목도 초록으로 보여줘서, 초보가 무엇을 확인해야 하는지 배우게 한다.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.disclosure import keypoints
from app.disclosure import repository as disclosure_repository
from app.disclosure import service as disclosure_service
from app.risk.schemas import Evidence, RiskCheck, RiskResponse
from app.valuation import repository as valuation_repository
from app.valuation import service as valuation_service

PERIOD_DAYS = 365
MAX_EVIDENCE = 5


@dataclass(frozen=True)
class DisclosureCheck:
    key: str
    title: str
    categories: tuple[str, ...]  # disclosure/keypoints.py의 category 이름
    level: str  # 해당 공시가 있으면 caution / danger
    why: str
    found: str  # 공시가 있을 때 한 줄 ({n}건)
    clean: str  # 없을 때 한 줄


DISCLOSURE_CHECKS = (
    DisclosureCheck(
        "listing", "상장 유지", ("상장폐지", "관리종목", "거래정지", "불성실공시"), "danger",
        "관리종목·거래정지·불성실공시는 거래소가 문제가 있다고 본 것이에요. 심하면 주식시장에서 퇴출(상장폐지)될 수 있어요.",
        "최근 1년 거래소 경고 관련 공시가 {n}건 있어요.",
        "최근 1년 관리종목·거래정지·불성실공시 관련 공시가 없어요.",
    ),
    DisclosureCheck(
        "trust", "회계·경영 신뢰", ("감사의견", "횡령·배임"), "danger",
        "회계법인이 장부를 믿기 어렵다고 하거나(감사의견), 회사 돈이 빼돌려지면(횡령·배임) 숫자 자체를 믿을 수 없게 돼요.",
        "감사의견·횡령·배임 관련 공시가 {n}건 있어요. 원문을 꼭 확인해 보세요.",
        "최근 1년 감사의견 문제나 횡령·배임 공시가 없어요.",
    ),
    DisclosureCheck(
        "survival", "회사 존속", ("회생·파산", "영업정지"), "danger",
        "회생절차·파산·영업정지는 회사가 계속 사업을 할 수 있는지가 걸린 일이에요.",
        "회생·파산·영업정지 관련 공시가 {n}건 있어요.",
        "최근 1년 회생·파산·영업정지 공시가 없어요.",
    ),
    DisclosureCheck(
        "dilution", "주식 수가 늘어날 일",
        ("유상증자", "전환사채(CB)", "신주인수권부사채(BW)", "전환가격 조정", "주식 수 증가", "감자"), "caution",
        "새 주식을 팔거나(유상증자) 주식으로 바뀔 빚(CB·BW)을 내면 주식 수가 늘어 내 몫이 작아질 수 있어요. "
        "전환가격을 낮추면(리픽싱) 더 많은 주식이 생겨요.",
        "최근 1년 주식 수가 늘어날 수 있는 공시가 {n}건 있어요.",
        "최근 1년 유상증자·전환사채 같은 공시가 없어요.",
    ),
    DisclosureCheck(
        "legal", "소송·제재·사고", ("소송", "벌금·제재", "중대재해", "계약 해지"), "caution",
        "소송·벌금·큰 사고·계약 해지는 회사 이익에 직접 영향을 줄 수 있어요. 금액이 회사 규모에 비해 큰지가 중요해요.",
        "소송·제재·사고·계약 해지 관련 공시가 {n}건 있어요. 금액을 확인해 보세요.",
        "최근 1년 소송·제재·사고 관련 공시가 없어요.",
    ),
    DisclosureCheck(
        "owner", "주인이 바뀌는 일", ("최대주주 변경",), "caution",
        "최대주주가 바뀌면 회사의 방향이 크게 달라질 수 있어요. 잦은 최대주주 변경은 그 자체로 주의 신호예요.",
        "최근 1년 최대주주 변경 공시가 {n}건 있어요.",
        "최근 1년 최대주주 변경이 없어요.",
    ),
)

BRIEF_HALT = "중요내용공시"  # 예: 매매거래정지및정지해제(중요내용공시)
STATUS_ORDER = {"danger": 0, "caution": 1, "ok": 2}


def get_by_stock(db: Session, code: str) -> RiskResponse:
    # 공시·재무 데이터를 최신으로 (각 도메인이 알아서 반나절~일주일 단위로만 새로 받는다)
    disclosure_service.get_by_stock(db, code, PERIOD_DAYS)
    if disclosure_repository.find_corp(db, code) is None:  # ETF처럼 DART에 회사로 등록되지 않은 종목
        return RiskResponse(available=False, message="회사가 아닌 종목(ETF 등)은 위험 신호 점검을 하지 않아요.")
    try:
        valuation_service.get_overview(db, code)
    except Exception as e:
        db.rollback()
        print(f"  위험 신호용 재무 갱신 실패({code}): {e!r}")

    since = date.today() - timedelta(days=PERIOD_DAYS)
    disclosures = [(d, keypoints.classify(d.report_nm)) for d in disclosure_repository.find_by_stock(db, code, since)]
    annual = sorted(valuation_repository.find_annual(db, code), key=lambda a: a.year)

    checks = [_loss_check(annual), _capital_check(annual)] + [_disclosure_check(c, disclosures) for c in DISCLOSURE_CHECKS]
    checks.sort(key=lambda c: STATUS_ORDER[c.status])  # 문제 있는 것부터 (같으면 원래 순서)
    counts = {s: sum(c.status == s for c in checks) for s in STATUS_ORDER}
    return RiskResponse(available=True, period_days=PERIOD_DAYS, checks=checks, counts=counts)


def _disclosure_check(c: DisclosureCheck, disclosures: list) -> RiskCheck:
    hits = [(d, rule) for d, rule in disclosures if rule.category in c.categories]
    # 이미 낸 공시를 고친 것([기재정정])은 같은 일이라 따로 세지 않는다
    originals = [(d, rule) for d, rule in hits if not keypoints.is_correction(d.report_nm)] or hits
    if not originals:
        return RiskCheck(key=c.key, title=c.title, status="ok", summary=c.clean, why=c.why)
    evidence = [
        Evidence(
            date=d.rcept_dt,
            text=f"[{rule.category}] {d.report_nm}",
            url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d.rcept_no}",
        )
        for d, rule in originals[:MAX_EVIDENCE]
    ]
    status, summary = c.level, c.found.format(n=len(originals))
    if all(BRIEF_HALT in d.report_nm for d, _ in originals):
        # 합병·분할 같은 중요한 발표 직전에 잠깐 거래를 멈춘 것: 문제가 생겨 멈춘 거래정지와는 다르다
        status = "caution"
        summary = f"중요한 발표 때문에 잠깐 거래가 멈춘 적이 {len(originals)}번 있어요. 문제가 생겨 멈춘 것과는 달라요. 무슨 발표였는지 보세요."
    return RiskCheck(key=c.key, title=c.title, status=status, summary=summary, why=c.why, evidence=evidence)


def _won(v: float) -> str:
    """원 단위 숫자를 '1.2조', '340억'처럼."""
    a = abs(v)
    s = f"{a / 1e12:.1f}조" if a >= 1e12 else f"{a / 1e8:,.0f}억"
    return ("-" if v < 0 else "") + s


def _loss_check(annual: list) -> RiskCheck:
    title = "이익을 내고 있나"
    why = "손실이 몇 년씩 이어지면 회사가 빚을 내거나 새 주식을 팔아 버티는 경우가 많아요(주식 수 증가로 이어짐)."
    rows = [a for a in annual if a.net_income is not None]
    if not rows:
        return RiskCheck(key="loss", title=title, status="ok", summary="연도별 순이익 정보가 아직 없어요.", why=why)
    streak = 0
    for a in reversed(rows):  # 최근 해부터 거꾸로 연속 손실 세기
        if a.net_income >= 0:
            break
        streak += 1
    loss_years = sum(a.net_income < 0 for a in rows)
    last = rows[-1]
    evidence = [Evidence(text=f"{a.year}년 순이익 {_won(a.net_income)}원") for a in rows[-5:][::-1]]
    if streak >= 3:
        status, summary = "danger", f"최근 {streak}년 연속 순손실이에요 (마지막 {last.year}년)."
    elif streak >= 1:
        status, summary = "caution", f"{last.year}년에 순손실을 냈어요" + (f" ({streak}년 연속)." if streak > 1 else ".")
    elif loss_years:
        status, summary = "ok", f"최근엔 이익을 내고 있어요. 지난 {len(rows)}년 중 손실을 낸 해는 {loss_years}번이에요."
    else:
        status, summary = "ok", f"지난 {len(rows)}년 동안 한 번도 순손실이 없었어요."
    return RiskCheck(key="loss", title=title, status=status, summary=summary, why=why, evidence=evidence)


def _capital_check(annual: list) -> RiskCheck:
    title = "빚이 재산보다 많은가"
    why = "자본(회사 재산 - 빚)이 마이너스면 자본잠식이에요. 빚이 재산보다 많다는 뜻이라 관리종목·상장폐지 사유가 될 수 있어요."
    rows = [a for a in annual if a.equity is not None]
    if not rows:
        return RiskCheck(key="capital", title=title, status="ok", summary="자본총계 정보가 아직 없어요.", why=why)
    last = rows[-1]
    evidence = [Evidence(text=f"{a.year}년 자본총계 {_won(a.equity)}원") for a in rows[-3:][::-1]]
    if last.equity < 0:
        status, summary = "danger", f"{last.year}년 자본총계가 마이너스예요(완전자본잠식)."
    elif len(rows) >= 2 and rows[-2].equity > 0 and last.equity < rows[-2].equity * 0.7:
        status, summary = "caution", f"{last.year}년 자본이 한 해 전보다 30% 넘게 줄었어요."
    else:
        status, summary = "ok", f"{last.year}년 자본총계 {_won(last.equity)}원으로 플러스예요."
    return RiskCheck(key="capital", title=title, status=status, summary=summary, why=why, evidence=evidence)
