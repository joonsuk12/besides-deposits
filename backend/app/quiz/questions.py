"""읽기 퀴즈 문제 만들기. Spring으로 치면 문제 유형마다 하나씩 있는 전략(Strategy) 클래스 묶음이다.

문제 문구는 문제 은행(quiz/bank.py)에 사람이 미리 써 두고, 여기서는 **관심종목의 실제 데이터**를 골라 끼워 넣는다.
- disclosure : 관심종목에 실제로 나온 공시 → "그래서 나에게 무슨 일이 / 무엇을 확인할까"
- valuation  : 관심종목의 지금 PER·PBR → 왜 높고 낮을 수 있나, 흔한 착각, PER이 움직이는 원리
- report     : 관심종목 리포트의 목표주가 변화·투자의견 → 어떻게 읽나
- per_change : 관심종목의 지난 해들 연말 PER 변화 → 주가 때문인가 이익 때문인가 (타임머신 데이터 재사용)

원칙
- 정답이 분명한 문제만. 주가 방향은 묻지 않는다.
- 문제는 (유형, 종목, 참조값)으로 똑같이 다시 만들 수 있다. 채점 때 서버가 다시 만들어 비교한다.
- 보기 key는 qid와 문장으로 만든 해시라 화면 코드에서 정답을 알 수 없다. 보기 순서도 qid로 정한 난수라 다시 만들어도 같다.
"""
import hashlib
import math
import random
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.disclosure import keypoints
from app.disclosure import repository as disclosure_repository
from app.quiz import bank
from app.quiz.bank import Template
from app.report import repository as report_repository
from app.stock import repository as stock_repository
from app.valuation import repository as valuation_repository
from app.valuation import service as valuation_service

TYPES = {
    "disclosure": "📢 공시 해석",
    "valuation": "📊 PER·PBR 해석",
    "report": "📄 리포트 해석",
    "per_change": "⏳ PER은 왜 바뀌었나",
}
DART = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo={}"


@dataclass
class Item:
    type: str
    code: str
    ref: str
    name: str
    prompt: str
    options: list[tuple[str, str]]  # (key, label)
    correct: str  # 정답 보기의 key
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
    if stock is None or stock.market == "ETF":
        return None
    fn = {"disclosure": _disclosure, "valuation": _valuation, "report": _report, "per_change": _per_change}.get(qtype)
    return fn(db, code, stock.name, ref, rng) if fn else None


def _key(qid: str, text: str) -> str:
    return hashlib.sha1(f"{qid}|{text}".encode()).hexdigest()[:8]


def _from_template(
    qtype: str, code: str, ref: str, name: str, t: Template, values: dict, rng: random.Random,
    correct_text: str | None = None, wrong_texts: list[str] | None = None, **extra,
) -> Item:
    """문제 틀에 값을 채우고 보기를 섞는다. 보기 key는 해시라 정답이 드러나지 않는다."""
    qid = f"{qtype}|{code}|{ref}"
    fill = lambda s: s.format(**values) if s else s  # noqa: E731
    correct = fill(correct_text if correct_text is not None else t.correct)
    wrongs = [fill(w) for w in (wrong_texts if wrong_texts is not None else t.wrongs)]
    texts = [correct] + wrongs
    rng.shuffle(texts)
    options = [(_key(qid, x), x) for x in texts]
    return Item(
        type=qtype,
        code=code,
        ref=ref,
        name=name,
        prompt=fill(t.prompt),
        options=options,
        correct=_key(qid, correct),
        explanation=fill(t.explanation),
        checks=[fill(c) for c in t.checks],
        note=fill(t.note),
        **extra,
    )


def _won(n: float) -> str:
    return f"{n:,.0f}"


# ── 공시 해석 ──────────────────────────────────────────


def _disclosure(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    rows = disclosure_repository.find_by_stock(db, code, date.today() - timedelta(days=365))
    rows = [d for d in rows if not keypoints.is_correction(d.report_nm)]
    by_cat: dict[str, list] = {}
    for d in rows:  # 최신순으로 온다
        cat = keypoints.classify(d.report_nm).category
        if cat == "다른 회사 투자" and "처분" in d.report_nm:  # 문제 틀이 '사는' 경우라 파는 공시는 뺀다
            continue
        if cat in bank.DISCLOSURE:
            by_cat.setdefault(cat, []).append(d)
    if not by_cat:
        return None
    counts = Counter({c: len(v) for c, v in by_cat.items()})

    def usable(cat: str, t: Template) -> bool:
        return "{count}" not in t.prompt or (counts[cat] >= 10 if t.tid == "insider-many" else counts[cat] >= 1)

    if ref:
        rcept_no, tid = ref.split(":")
        d = next((x for v in by_cat.values() for x in v if x.rcept_no == rcept_no), None)
        if d is None:
            return None
        cat = keypoints.classify(d.report_nm).category
        t = next((t for t in bank.DISCLOSURE[cat] if t.tid == tid), None)
        if t is None:
            return None
    else:
        # 공시 종류를 먼저 고른다 (임원 보고처럼 수천 건인 종류만 계속 나오지 않게)
        cat = rng.choice(sorted(by_cat))
        templates = [t for t in bank.DISCLOSURE[cat] if usable(cat, t)]
        if not templates:
            return None
        t = rng.choice(templates)
        d = by_cat[cat][0] if "{count}" in t.prompt else rng.choice(by_cat[cat][:5])  # 최근 것 위주
    values = {"name": name, "title": d.report_nm, "date": d.rcept_dt.strftime("%Y-%m-%d"), "count": counts[cat]}
    return _from_template("disclosure", code, f"{d.rcept_no}:{t.tid}", name, t, values, rng, link=DART.format(d.rcept_no))


# ── PER·PBR 해석 ───────────────────────────────────────


def _valuation(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    v = valuation_service.get_by_stock(db, code)
    if not v.available:
        return None
    me = valuation_repository.find(db, code)
    industry = (me.industry_name if me else None) or ""
    per, ind = v.per, v.industry_per
    situations: dict[str, Template] = {}
    if per and per >= 100:
        situations[bank.PER_HUGE.tid] = bank.PER_HUGE
    elif per and ind and per < ind * 0.7:
        t = bank.PER_LOW_CYCLE if v.focus == "both" else bank.PER_LOW
        situations[t.tid] = t
    elif per and ind and per > ind * 1.3:
        situations[bank.PER_HIGH.tid] = bank.PER_HIGH
    if per and per < 100:
        situations[bank.PER_MOVE.tid] = bank.PER_MOVE
    if v.pbr and v.focus == "pbr" and any(w in industry for w in ("복합", "지주")):
        situations[bank.PBR_HOLDING.tid] = bank.PBR_HOLDING
    if not situations:
        return None
    tid = ref if ref else rng.choice(sorted(situations))
    t = situations.get(tid)
    if t is None:
        return None
    values = {
        "name": name,
        "per": f"{per:.1f}" if per else "-",
        "pbr": f"{v.pbr:.2f}" if v.pbr else "-",
        "ind_per": f"{ind:.1f}" if ind else "-",
        "eps": _won(v.eps) if v.eps else "-",
        "price": _won(v.price) if v.price else "-",
        "up": f"{per * 1.2:.1f}" if per else "-",
        "down": f"{per * 0.8:.1f}" if per else "-",
        "double": f"{per * 2:.1f}" if per else "-",
    }
    context = []
    if v.price_date:
        context.append(f"{v.price_date:%Y-%m-%d} 종가 기준")
    return _from_template("valuation", code, tid, name, t, values, rng, context=context)


# ── 리포트 해석 ─────────────────────────────────────────


def _report(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    reports = [r for r in report_repository.find_by_stock(db, code, 40) if r.write_date >= date.today() - timedelta(days=180)]
    cands: list[tuple] = []  # (report, template, prev)
    for r in reports:
        prev = report_repository.find_previous_goal(db, r) if r.goal_price else None
        if prev and r.goal_price and r.goal_price < prev and r.opinion_type == "buy":
            cands.append((r, bank.REPORT_DOWN_BUY, prev))
        elif prev and r.goal_price and r.goal_price > prev:
            cands.append((r, bank.REPORT_UP, prev))
        if r.opinion_type == "neutral":
            cands.append((r, bank.REPORT_NEUTRAL, prev))
    if ref:
        nid, tid = ref.split(":")
        cands = [c for c in cands if c[0].nid == nid and c[1].tid == tid]
    if not cands:
        return None
    if ref:
        r, t, prev = cands[0]
    else:
        tid = rng.choice(sorted({c[1].tid for c in cands}))  # 종류를 먼저 골라 한쪽으로 쏠리지 않게
        r, t, prev = rng.choice([c for c in cands if c[1].tid == tid])
    values = {
        "name": name,
        "broker": r.broker,
        "date": r.write_date.strftime("%Y-%m-%d"),
        "goal": _won(r.goal_price) if r.goal_price else "-",
        "prev": _won(prev) if prev else "-",
        "opinion": r.opinion or {"buy": "매수", "neutral": "중립", "sell": "매도"}.get(r.opinion_type or "", "중립"),
    }
    return _from_template("report", code, f"{r.nid}:{t.tid}", name, t, values, rng)


# ── PER은 왜 바뀌었나 ──────────────────────────────────


def _per_change(db: Session, code: str, name: str, ref: str | None, rng: random.Random) -> Item | None:
    annual = {a.year: a for a in valuation_repository.find_annual(db, code)}
    shares = valuation_service.split_adjusted_shares(db, code)
    year_end: dict[int, int] = {}
    for p in stock_repository.find_prices(db, code, date(2000, 1, 1)):
        year_end[p.date.year] = p.close  # 날짜순이라 마지막 값이 그해 마지막 거래일
    cands = []
    for y1 in sorted(annual):
        y0 = y1 - 1
        a0, a1 = annual.get(y0), annual.get(y1)
        if not (a0 and a1 and a0.net_income and a1.net_income and a0.net_income > 0 and a1.net_income > 0):
            continue
        if not (shares.get(y0) and shares.get(y1) and year_end.get(y0) and year_end.get(y1)):
            continue
        eps0, eps1 = a0.net_income / shares[y0], a1.net_income / shares[y1]
        per0, per1 = year_end[y0] / eps0, year_end[y1] / eps1
        if abs(math.log(per1 / per0)) < math.log(1.4):  # 40% 넘게 바뀐 해만 (차이가 분명해야 정답도 분명하다)
            continue
        pf, ef = year_end[y1] / year_end[y0], eps1 / eps0
        if abs(abs(math.log(pf)) - abs(math.log(ef))) < math.log(1.15):  # 주가·이익 영향이 비슷하면 정답이 애매해서 뺀다
            continue
        cands.append((y0, y1, per0, per1, pf, ef))
    if ref:
        cands = [c for c in cands if str(c[1]) == ref]
    if not cands:
        return None
    y0, y1, per0, per1, pf, ef = cands[0] if ref else rng.choice(cands)
    if abs(math.log(pf)) >= abs(math.log(ef)):
        correct = "price-up" if pf > 1 else "price-down"
    else:
        correct = "earn-up" if ef > 1 else "earn-down"
    t = bank.PER_CHANGE
    values = {
        "name": name,
        "y0": y0,
        "y1": y1,
        "per0": f"{per0:.1f}",
        "per1": f"{per1:.1f}",
        "word": "높아졌어요" if per1 > per0 else "낮아졌어요",
        "price_change": f"{year_end[y0]:,}원 → {year_end[y1]:,}원({pf - 1:+.0%})",
        "eps_change": f"{(pf / (per1 / per0)) - 1:+.0%}",
    }
    labels = bank.PER_CHANGE_OPTIONS
    item = _from_template(
        "per_change",
        code,
        str(y1),
        name,
        t,
        values,
        rng,
        correct_text=labels[correct],
        wrong_texts=[labels[k] for k in labels if k != correct],
        context=[
            f"{y0}년 말 주가 {year_end[y0]:,}원 → {y1}년 말 {year_end[y1]:,}원 ({pf - 1:+.0%})",
            f"1주당 1년 이익(EPS) {y0}년 → {y1}년: {ef - 1:+.0%}",
            "PER = 주가 ÷ 1주당 이익",
        ],
    )
    return item
