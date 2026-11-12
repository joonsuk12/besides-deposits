"""뉴스에서 키포인트를 규칙으로 뽑는다 (유료 AI 없이).

- 중요도: 같은 내용을 다룬 기사 수 (네이버 묶음 크기). 많이 다룰수록 중요.
- 한 줄 요약: 본문 미리보기의 첫 문장
- 분위기: 좋은 소식·나쁜 소식을 나타내는 단어로 추정 (정확하지 않으니 '추정'으로 표시)
- 주제: 실적, 수주, 신제품 같은 꼬리표
"""
import re

from app.core.text import shorten

_POSITIVE = ("상승", "급등", "강세", "최대", "최고", "호실적", "흑자", "수주", "계약", "승인", "개선", "증가",
             "확대", "돌파", "신고가", "상향", "수혜", "기대", "성장", "회복", "반등", "호조")
_NEGATIVE = ("하락", "급락", "약세", "적자", "손실", "부진", "감소", "우려", "리스크", "소송", "제재", "리콜",
             "하향", "철회", "지연", "악화", "충격", "경고", "취소", "신저가", "매도")

TOPICS: dict[str, tuple[str, ...]] = {
    "실적": ("실적", "영업이익", "매출", "순이익", "분기", "어닝"),
    "수주·계약": ("수주", "계약", "공급", "납품"),
    "신제품·기술": ("출시", "신제품", "개발", "기술", "특허", "공개"),
    "투자·증설": ("투자", "증설", "공장", "설비", "인수", "M&A"),
    "주주환원": ("배당", "자사주", "주주환원", "소각"),
    "증권사 의견": ("목표주가", "투자의견", "리포트", "증권"),
    "규제·소송": ("규제", "소송", "제재", "조사", "과징금"),
    "수급": ("외국인", "기관", "개인", "순매수", "순매도", "공매도"),
}


def summary(body: str) -> str:
    text = re.sub(r"\s+", " ", body or "").strip().rstrip(".… ")
    first = re.split(r"(?<=[다요])\.\s", text, maxsplit=1)[0]
    return shorten(first, 120)


def tone(title: str, body: str) -> str:
    """'good' / 'bad' / 'neutral'. 제목에 가중치를 둔 단어 세기."""
    text = f"{title} {title} {body}"
    pos = sum(text.count(w) for w in _POSITIVE)
    neg = sum(text.count(w) for w in _NEGATIVE)
    if pos >= neg + 2:
        return "good"
    if neg >= pos + 2:
        return "bad"
    return "neutral"


def topics(title: str, body: str) -> list[str]:
    text = f"{title} {body}"
    return [name for name, words in TOPICS.items() if any(w in text for w in words)][:3]
