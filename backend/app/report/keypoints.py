"""증권사 리포트 요약문에서 초보가 봐야 할 부분을 규칙으로 뽑는다 (유료 AI 없이).

뽑는 것
- 한 줄 결론: 증권사가 요약문 맨 위에 굵게 단 소제목
- 핵심 근거: 숫자와 판단이 들어간 문장 중 점수가 높은 3개 (원래 순서 유지)
- 조심할 점: 우려·부진·하락 같은 말이 들어간 문장
- 용어 풀이: 요약문에 나온 어려운 용어를 쉬운 말로

Spring으로 치면 상태 없는 유틸 클래스(@Component)다. DB를 모르고 글만 받아서 결과를 돌려준다.
"""
import re
from dataclasses import dataclass, field

from app.core.text import first_strong, html_to_lines, shorten, split_sentences

# 초보에게 낯선 용어 → 쉬운 설명. 요약문에 나온 것만 골라서 보여준다.
GLOSSARY: dict[str, str] = {
    "목표주가": "증권사가 앞으로 6개월~1년 안에 갈 수 있다고 보는 주가",
    "투자의견": "증권사가 이 주식을 어떻게 보는지 한 단어로 정리한 것 (매수·중립·매도 등)",
    "컨센서스": "여러 증권사 예상치의 평균. 실적이 이보다 좋으면 '상회', 나쁘면 '하회'",
    "상회": "예상보다 좋게 나왔다는 뜻",
    "하회": "예상보다 나쁘게 나왔다는 뜻",
    "YoY": "작년 같은 기간과 비교 (Year on Year)",
    "QoQ": "바로 전 분기와 비교 (Quarter on Quarter)",
    "영업이익률": "매출 100원 중 본업으로 남긴 이익이 몇 원인지",
    "영업이익": "회사가 본업(물건·서비스 판매)으로 번 이익",
    "순이익": "모든 비용과 세금을 빼고 최종적으로 남은 이익",
    "PER": "주가가 1년 이익의 몇 배인지. 낮을수록 이익에 비해 싸다는 뜻",
    "P/E": "PER과 같은 말. 주가가 1년 이익의 몇 배인지",
    "PBR": "주가가 회사 순자산의 몇 배인지. 1보다 낮으면 장부가치보다 싸게 거래된다는 뜻",
    "P/B": "PBR과 같은 말. 주가가 회사 순자산의 몇 배인지",
    "EPS": "주식 1주가 1년 동안 벌어들인 이익",
    "BPS": "주식 1주에 해당하는 회사 순자산",
    "ROE": "회사가 자기 돈(자본)으로 1년에 몇 %를 벌었는지. 높을수록 효율적",
    "EV/EBITDA": "회사 전체 가치가 현금성 이익의 몇 배인지. 낮을수록 싸다는 뜻",
    "밸류에이션": "주가가 비싼지 싼지 따져보는 일",
    "멀티플": "PER·PBR처럼 '몇 배'로 가치를 매기는 기준",
    "커버리지": "증권사가 이 종목을 정기적으로 분석하기 시작했다는 뜻 (커버리지 개시)",
    "업사이드": "현재 주가에서 목표주가까지 오를 여지",
    "상승여력": "현재 주가에서 목표주가까지 오를 여지",
    "턴어라운드": "적자나 부진에서 벗어나 실적이 좋아지는 전환점",
    "가이던스": "회사가 직접 발표한 앞으로의 실적 전망",
    "어닝 서프라이즈": "실적이 예상보다 크게 좋게 나온 것",
    "어닝 쇼크": "실적이 예상보다 크게 나쁘게 나온 것",
    "모멘텀": "주가를 움직일 만한 계기나 흐름",
    "펀더멘털": "실적·재무 같은 회사의 기초 체력",
    "리레이팅": "시장이 회사 가치를 더 높게 쳐주기 시작하는 것",
    "디레이팅": "시장이 회사 가치를 더 낮게 보기 시작하는 것",
    "다운사이클": "업황이 나빠지는 구간",
    "업사이클": "업황이 좋아지는 구간",
    "HBM": "AI 반도체에 들어가는 고성능 메모리",
    "DRAM": "컴퓨터·서버의 주 메모리 반도체",
    "NAND": "저장용 메모리 반도체 (SSD 등)",
    "ASP": "제품 평균 판매가격",
    "OPM": "영업이익률. 매출 중 본업 이익의 비율",
    "CAPEX": "공장·설비에 쓰는 투자 금액",
    "수주잔고": "이미 받아 놓은 주문 중 아직 매출로 잡히지 않은 금액",
    "주주환원": "배당이나 자사주 매입으로 주주에게 이익을 돌려주는 것",
    "자사주": "회사가 사들인 자기 회사 주식",
    "배당수익률": "주가 대비 1년 배당금 비율",
    "시가총액": "주가 × 주식 수. 시장이 매긴 회사 전체 값",
    "실적 추정치": "증권사가 예상한 앞으로의 매출·이익",
}

# 문장 점수에 쓰는 말
_JUDGE_WORDS = ("전망", "예상", "기대", "상향", "하향", "상회", "하회", "개선", "성장", "증가", "확대",
                "수혜", "회복", "견조", "호조", "목표주가", "투자의견", "제시", "유지", "실적", "영업이익", "매출")
_RISK_WORDS = ("우려", "리스크", "위험", "부담", "둔화", "부진", "악화", "감소", "하락", "불확실", "지연",
               "손실", "적자", "약세", "하향", "역성장", "경쟁 심화")
_NUMBER = re.compile(r"\d[\d,.]*\s*(%|%p|원|조|억|만|배|bp)")
_LEGAL = ("Compliance", "본 자료", "당사는", "투자판단", "무단")


@dataclass
class ReportKeyPoints:
    headline: str | None
    points: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    terms: list[tuple[str, str]] = field(default_factory=list)


_HANGUL = re.compile(r"[가-힣]")
_GOOD_WORDS = ("회복", "개선", "성장", "증가", "상향", "기대", "호조", "견조", "확대")


def extract(content_html: str, title: str) -> ReportKeyPoints:
    headline = first_strong(content_html)
    sentences = [s for s in split_sentences(html_to_lines(content_html)) if not s.startswith(_LEGAL)]
    if headline:
        sentences = [s for s in sentences if s != headline]
        # "WHAT'S THE STORY?", "3Q Review" 같은 영어 꼬리표는 결론이 아니다
        if not _HANGUL.search(headline) or len(headline) < 6:
            headline = None

    def is_risk(s: str) -> bool:
        bad = sum(w in s for w in _RISK_WORDS)
        good = sum(w in s for w in _GOOD_WORDS)
        return bad > 0 and bad >= good

    risks = [shorten(s, 140) for s in sentences if is_risk(s)][:2]

    scored = []
    for i, s in enumerate(sentences):
        score = 2 * len(_NUMBER.findall(s)) + sum(w in s for w in _JUDGE_WORDS)
        if len(s) > 220:
            score -= 1
        scored.append((score, i, s))
    top = sorted(scored, key=lambda x: (-x[0], x[1]))[:3]
    points = [shorten(s, 160) for _, _, s in sorted(top, key=lambda x: x[1]) if s not in risks]

    full_text = " ".join([title, headline or "", *sentences])
    terms = [(term, desc) for term, desc in GLOSSARY.items() if term in full_text][:6]

    return ReportKeyPoints(headline=headline or title, points=points, risks=risks, terms=terms)


OPINION_KO = {"buy": "매수", "neutral": "중립", "sell": "매도"}


def opinion_label(opinion: str | None, opinion_type: str | None) -> str | None:
    """증권사마다 다른 표기(Buy, Outperform, 매수 …)를 초보가 알아보기 쉽게."""
    if not opinion:
        return None
    ko = OPINION_KO.get(opinion_type or "")
    return f"{ko} ({opinion})" if ko and ko not in opinion else opinion
