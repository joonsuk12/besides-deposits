"""읽기 퀴즈 문제 만들기 (유료 AI 없이, 이미 있는 규칙과 데이터로). Spring으로 치면 문제 유형마다 하나씩 있는 전략(Strategy) 클래스 묶음이다.

원칙: **정답이 분명한 문제만** 낸다. 주가 방향을 맞히는 문제는 내지 않는다 (2026-11-25 타임머신 평가: 운에 가깝다).
"이 공시는 무슨 뜻인가", "이 업종은 무엇을 먼저 보나", "업종보다 비싼가"처럼 읽는 법을 묻고, 정답 근거는 화면에 이미 있는 규칙이다.
- disclosure : 공시 이름 → 뜻 (disclosure/keypoints.py 규칙)
- risk       : 공시 → 위험 신호 점검의 어느 항목 (risk/service.py 항목)
- focus      : 업종 → PER·PBR 중 무엇을 먼저 (valuation/focus.py 가이드)
- peer       : 이 종목 PER(PBR) vs 업종 → 낮은/비슷/높은 편 (±15%, 주가 수준 카드와 같은 기준)
- upside     : 리포트 목표주가 vs 그날 종가 → 상승여력 구간
- then       : 과거 어느 날 PER vs 그 회사 평소 범위 → 낮은/비슷/높은 편 (타임머신 계산 재사용)

문제는 (유형, 종목, 참조값)만 있으면 똑같이 다시 만들 수 있다. 그래서 답을 채점할 때 서버가 다시 만들어 정답을 비교한다.
보기 순서도 qid로 정한 난수라서 다시 만들어도 같다.
"""
import random
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.disclosure import keypoints
from app.disclosure import repository as disclosure_repository
from app.report import repository as report_repository
from app.risk.service import DISCLOSURE_CHECKS
from app.stock import repository as stock_repository
from app.valuation import focus
from app.valuation import repository as valuation_repository
from app.valuation import service as valuation_service

TYPES = {
    "disclosure": "📢 공시 읽기",
    "risk": "🚦 위험 신호 분류",
    "focus": "🏭 업종별로 볼 지표",
    "peer": "⚖️ 업종과 비교",
    "upside": "🎯 목표주가 읽기",
    "then": "⏳ 그때 사실 읽기",
}
LEVEL_WORD = {"warn": "꼭 확인할 소식", "good": "보통 좋게 보는 소식", "key": "내용을 봐야 아는 중요한 소식", "info": "참고용"}
DART = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo={}"
SIMILAR = 0.15  # 주가 수준 카드와 같은 ±15% 기준
LEVEL3 = [("low", "업종보다 낮은 편"), ("similar", "업종과 비슷"), ("high", "업종보다 높은 편")]
# 뜻이 비슷해서 오답 보기로 같이 내면 헷갈리기만 하는 공시 묶음 (정답과 같은 묶음은 오답 보기로 쓰지 않는다)
SIMILAR_GROUPS = (
    {"자사주 매입", "주식 소각", "자사주 처분", "자사주 신탁 종료"},
    {"유상증자", "전환사채(CB)", "신주인수권부사채(BW)", "교환사채(EB)", "전환가격 조정", "주식 수 증가", "사채 미리 갚기"},
    {"공급 계약", "계약 해지"},
    {"무상증자", "감자", "유상감자", "주식 쪼개기·합치기"},
    {"실적 발표", "실적 큰 변화", "실적 발표 예고"},
    {"상장폐지", "관리종목", "거래정지", "불성실공시"},
)


def _josa(word: str, with_final: str, without_final: str) -> str:
    """받침이 있으면 앞의 조사, 없으면 뒤의 조사 (대신증권이 / 키움증권이 / 하나증권이 …)."""
    last = word[-1]
    has_final = "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 != 0
    return word + (with_final if has_final else without_final)


@dataclass
class Item:
    type: str
    code: str
    ref: str
    name: str
    prompt: str
    options: list[tuple[str, str]]  # (key, label)
    correct: str
    explanation: str
    context: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    note: str | None = None
    link: str | None = None

    @property
    def qid(self) -> str:
        return f"{self.type}|{self.code}|{self.ref}"


def build(db: Session, qtype: str, code: str, ref: str | None, rng: random.Random) -> Item | None:
    """ref가 없으면 새로 고르고, 있으면 그 문제를 그대로 다시 만든다."""
    stock = stock_repository.find_stock(db, code)
    if stock is None:
        return None
    fn = {
        "disclosure": _disclosure,
        "risk": _risk,
        "focus": _focus,
        "peer": _peer,
        "upside": _upside,
        "then": _then,
    }.get(qtype)
    return fn(db, code, stock.name, ref, rng) if fn else None


def _ordered(rng: random.Random, options: list[tuple[str, str]]) -> list[tuple[str, str]]:
    out = options[:]
    rng.shuffle(out)
    return out


def _three_way(ratio: float) -> str:
    return "low" if ratio < 1 - SIMILAR else "high" if ratio > 1 + SIMILAR else "similar"


# ── 공시 읽기 ──────────────────────────────────────────


def _recent_disclosures(db: Session, code: str, days: int) -> list:
    rows = disclosure_repository.find_by_stock(db, code, date.today() - timedelta(days=days))
    return [d for d in rows if not keypoints.is_correction(d.report_nm)]


def _disclosure(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    rows = [d for d in _recent_disclosures(db, code, 120) if keypoints.classify(d.report_nm).category != "기타"]
    rows = [d for d in rows if keypoints.classify(d.report_nm).level != "info"] or rows  # 참고용보다 중요한 공시를 먼저
    if ref:
        rows = [d for d in rows if d.rcept_no == ref]
    if not rows:
        return None
    d = rows[0] if ref else rng.choice(rows)
    rule = keypoints.classify(d.report_nm)
    group = next((g for g in SIMILAR_GROUPS if rule.category in g), {rule.category})
    others = [r for r in keypoints.RULES if r.category not in group and r.category != rule.category and r.level != "info"]
    picks = rng.sample(others, 3)
    options = _ordered(rng, [(rule.category, rule.explain)] + [(r.category, r.explain) for r in picks])
    return Item(
        type="disclosure",
        code=code,
        ref=d.rcept_no,
        name=name,
        prompt=f"{d.rcept_dt:%Y-%m-%d} {name}에서 '{d.report_nm}' 공시가 나왔어요. 이 공시는 무슨 뜻일까요?",
        options=options,
        correct=rule.category,
        explanation=f"'{rule.category}' 공시예요. " + (rule.why or rule.explain),  # 보기 문장은 화면에 이미 있어서 이유만
        checks=list(rule.checks),
        note=f"이런 공시는 보통 '{LEVEL_WORD.get(rule.level, rule.level)}'으로 봐요. 공시 이름의 핵심 단어({rule.words[0]})를 기억해 두면 다음엔 이름만 보고도 알 수 있어요.",
        link=DART.format(d.rcept_no),
    )


# ── 위험 신호 분류 ────────────────────────────────────


def _risk(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    by_category = {cat: c for c in DISCLOSURE_CHECKS for cat in c.categories}
    rows = [d for d in _recent_disclosures(db, code, 365) if keypoints.classify(d.report_nm).category in by_category]
    if ref:
        rows = [d for d in rows if d.rcept_no == ref]
    if not rows:
        return None
    d = rows[0] if ref else rng.choice(rows)
    rule = keypoints.classify(d.report_nm)
    check = by_category[rule.category]
    others = [c for c in DISCLOSURE_CHECKS if c.key != check.key]
    picks = rng.sample(others, 3)
    options = _ordered(rng, [(check.key, check.title)] + [(c.key, c.title) for c in picks])
    return Item(
        type="risk",
        code=code,
        ref=d.rcept_no,
        name=name,
        prompt=f"{name}의 '{d.report_nm}' 공시({d.rcept_dt:%Y-%m-%d})는 위험 신호 점검의 어느 항목에 들어갈까요?",
        options=options,
        correct=check.key,
        explanation=f"'{rule.category}' 공시는 '{check.title}' 항목이에요. {check.why}",
        checks=list(rule.checks),
        note="종목 화면 오른쪽 🚦 위험 신호 점검 카드에서 이 종목의 다른 항목도 확인해 보세요.",
        link=DART.format(d.rcept_no),
    )


# ── 업종별로 볼 지표 ───────────────────────────────────

FOCUS_OPTIONS = [
    ("per", "PER을 먼저 (이익을 봐요)"),
    ("pbr", "PBR을 먼저 (자산을 봐요)"),
    ("both", "PER과 PBR을 같이 (업황 따라 이익이 크게 바뀌어요)"),
    ("none", "둘 다 잘 안 맞아요 (다른 것을 봐요)"),
]


def _focus(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    me = valuation_repository.find(db, code)
    if me is None or not me.industry_name:
        return None
    guide = focus.decide(me.industry_name, None)  # 적자 여부와 상관없이 업종 원래 기준을 묻는다
    return Item(
        type="focus",
        code=code,
        ref="",
        name=name,
        prompt=f"{name}의 업종은 '{me.industry_name}'. 이 업종 주가가 비싼지 싼지 볼 때 무엇을 먼저 볼까요?",
        options=FOCUS_OPTIONS,
        correct=guide.focus,
        explanation=f"{guide.title}. {guide.reason}",
        checks=list(guide.also[:3]),
        note=guide.caution,
    )


# ── 업종과 비교 ───────────────────────────────────────


def _peer(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    v = valuation_service.get_by_stock(db, code)
    if not v.available:
        return None
    choices = [m for m in ("per", "pbr") if getattr(v, m) and getattr(v, f"industry_{m}")]
    if ref:
        choices = [m for m in choices if m == ref]
    if not choices:
        return None
    metric = choices[0] if ref else rng.choice(choices)
    mine, theirs = getattr(v, metric), getattr(v, f"industry_{metric}")
    label = metric.upper()
    correct = _three_way(mine / theirs)
    word = dict(LEVEL3)[correct]
    note = "업종보다 낮다고 무조건 싼 건 아니에요. 이익이 줄 거라고 보는 사람이 많아서 낮을 수도 있어요. 높다고 비싸기만 한 것도 아니에요(성장 기대)."
    if v.focus and v.focus != "both" and v.focus != metric:
        note = f"참고로 이 업종은 {v.focus.upper()}를 먼저 보는 업종이에요. " + note
    return Item(
        type="peer",
        code=code,
        ref=metric,
        name=name,
        prompt=f"{name}의 {label}은 {mine:g}배, 같은 업종({v.industry_name}) 주요 회사들의 {label} 중간값은 {theirs:g}배예요. 이 종목 {label}은?",
        context=[f"차이 기준: 업종 값의 ±15% 안이면 '비슷', 그보다 낮으면 '낮은 편', 높으면 '높은 편'"],
        options=LEVEL3,
        correct=correct,
        explanation=f"{mine:g} ÷ {theirs:g} = {mine / theirs:.2f} → 업종의 {mine / theirs * 100:.0f}% 수준이라 '{word}'이에요.",
        checks=[f"{label}이 무엇인지: " + ("주가가 1년 이익의 몇 배인지" if metric == "per" else "주가가 회사 순자산의 몇 배인지")],
        note=note,
    )


# ── 목표주가 읽기 ─────────────────────────────────────

UPSIDE_OPTIONS = [
    ("neg", "지금 주가보다 낮아요 (마이너스)"),
    ("lt10", "0~10%"),
    ("10to30", "10~30%"),
    ("30to50", "30~50%"),
    ("gt50", "50% 넘게"),
]


def _upside_bucket(u: float) -> str:
    return "neg" if u < 0 else "lt10" if u < 10 else "10to30" if u < 30 else "30to50" if u < 50 else "gt50"


def _upside(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    reports = [r for r in report_repository.find_by_stock(db, code, 30) if r.goal_price]
    reports = [r for r in reports if r.write_date >= date.today() - timedelta(days=120)]
    if ref:
        reports = [r for r in reports if r.nid == ref]
    if not reports:
        return None
    r = reports[0] if ref else rng.choice(reports)
    prices = [p for p in stock_repository.find_prices(db, code, r.write_date - timedelta(days=10)) if p.date <= r.write_date]
    if not prices:
        return None
    close = prices[-1].close
    upside = (r.goal_price / close - 1) * 100
    opinion = f" 투자의견은 '{r.opinion}'이에요." if r.opinion else ""
    return Item(
        type="upside",
        code=code,
        ref=r.nid,
        name=name,
        prompt=f"{r.write_date:%Y-%m-%d} {_josa(r.broker, '이', '가')} {name} 목표주가를 {r.goal_price:,}원으로 냈어요. 그날 종가는 {close:,}원이에요. 증권사가 보는 '오를 여지(상승여력)'는 얼마쯤일까요?",
        context=["상승여력 = (목표주가 ÷ 지금 주가 − 1) × 100"],
        options=UPSIDE_OPTIONS,
        correct=_upside_bucket(upside),
        explanation=f"({r.goal_price:,} ÷ {close:,} − 1) × 100 = {upside:+.1f}%예요.{opinion}",
        checks=["목표주가는 보통 6개월~1년 안에 갈 수 있다고 보는 값이에요", "같은 증권사의 지난번 목표주가와 비교해 올렸는지 내렸는지도 보세요"],
        note="목표주가는 증권사의 예상일 뿐 맞는다는 보장이 없어요. 증권사 리포트는 대부분 '매수' 의견이라, 의견보다 목표주가를 올렸는지 내렸는지가 더 많은 걸 알려줘요.",
    )


# ── 그때 사실 읽기 (타임머신 계산 재사용) ──────────────


def _then(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    from app.practice import service as practice_service

    prices = stock_repository.find_prices(db, code, date(2000, 1, 1))
    if len(prices) < 400:
        return None
    if ref:
        idx = [k for k, p in enumerate(prices) if p.date.isoformat() == ref]
        candidates = idx
    else:
        candidates = rng.sample(range(260, len(prices) - 1), min(25, len(prices) - 261))
    for i in candidates:
        v = practice_service.then_valuation(db, code, prices, i)
        if not v:
            continue
        past, per = v["past"], v["per"]
        avg = sum(past) / len(past)
        correct = "low" if per < avg * 0.85 else "high" if per > avg * 1.15 else "similar"
        words = {"low": "평소보다 낮은 편", "similar": "평소와 비슷", "high": "평소보다 높은 편"}
        after = v["after"]
        note = "이건 '그때 비쌌나 쌌나'를 읽는 연습이에요. 싸 보였다고 꼭 올랐던 건 아니에요."
        if after is not None:
            note = f"참고로 그 뒤 6개월 동안 주가는 {after:+.1f}% 움직였어요. " + note
        return Item(
            type="then",
            code=code,
            ref=prices[i].date.isoformat(),
            name=name,
            prompt=f"{prices[i].date:%Y-%m-%d} {name}의 PER은 {per:.1f}배였어요({v['last_year']}년 이익 기준). 이 회사의 지난 해들 연말 PER과 비교하면?",
            context=[f"지난 해들 연말 PER: " + ", ".join(f"{y}년 {p:g}배" for y, p in zip(v["years"], past)), f"평균 {avg:.1f}배 (±15% 안이면 '비슷')"],
            options=[(k, words[k]) for k in ("low", "similar", "high")],
            correct=correct,
            explanation=f"{per:.1f}배 ÷ 평균 {avg:.1f}배 = {per / avg:.2f} → '{words[correct]}'이에요. 같은 회사의 평소 수준과 견주면 지금이 비싼 편인지 싼 편인지 감이 와요.",
            checks=["업종 평균과도 비교해 보세요 (회사마다 평소 PER이 달라요)", "이익이 크게 줄어든 해에는 PER이 갑자기 높아져요"],
            note=note,
        )
    return None
