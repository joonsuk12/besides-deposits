"""업종에 따라 PER과 PBR 중 무엇을 더 보는지 알려주는 규칙 (유료 AI 없이, 업종 이름으로).

Spring으로 치면 상수 테이블 + 작은 정책 클래스다. report/keypoints.py, disclosure/keypoints.py와 같은 방식:
위에서부터 먼저 맞는 규칙 하나를 쓴다. 업종 이름은 네이버 업종 분류(예: "반도체와반도체장비", "은행")를 그대로 쓴다.

focus
- per  : 이익을 보는 업종 (PER 위주)
- pbr  : 자산을 보는 업종 (PBR 위주)
- both : 상황에 따라 둘 다 (업황에 따라 이익이 크게 바뀌는 업종)
- none : 둘 다 잘 맞지 않는 업종 (적자가 흔한 바이오 등)
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Focus:
    words: tuple[str, ...]
    focus: str
    title: str
    reason: str


RULES: tuple[Focus, ...] = (
    Focus(
        ("은행", "증권", "보험", "기타금융", "카드", "창업투자", "캐피탈"),
        "pbr",
        "금융 업종은 PBR을 주로 봐요",
        "금융회사는 가진 돈(대출·투자 자산)이 곧 사업이라, 자산에 비해 주가가 어떤지(PBR)를 주로 봐요. "
        "자기자본으로 1년에 얼마를 버는지(ROE)가 높을수록 PBR이 높게 매겨지는 편이에요.",
    ),
    Focus(
        ("복합기업", "지주"),
        "pbr",
        "지주회사는 PBR을 주로 봐요",
        "다른 회사 지분을 많이 가진 회사라, 가진 자산 가치에 비해 주가가 얼마나 낮은지(PBR, '지주사 할인')를 주로 봐요. "
        "자회사 실적이 함께 잡혀서 PER은 들쭉날쭉할 수 있어요.",
    ),
    Focus(
        ("철강", "비철금속", "화학", "조선", "해운", "건설", "석유", "가스", "종이", "목재", "건축자재", "운송인프라"),
        "pbr",
        "경기에 민감한 업종이라 PBR을 더 봐요",
        "경기에 따라 이익이 크게 오르내리는 업종이에요. 이익이 들쭉날쭉하면 PER도 크게 흔들려서, "
        "공장·설비 같은 자산을 기준으로 한 PBR을 더 믿을 만한 기준으로 봐요.",
    ),
    Focus(
        ("반도체", "디스플레이"),
        "both",
        "반도체는 업황에 따라 PER·PBR을 같이 봐요",
        "반도체 가격에 따라 이익이 크게 변해요. 호황엔 이익이 커서 PER이 낮아 보이고, 불황엔 이익이 줄어 PER이 높아 보여요. "
        "그래서 업황이 나쁠 땐 PBR을, 좋을 땐 PER과 증권사 예상 이익(추정 PER)을 함께 봐요.",
    ),
    Focus(
        ("생물공학", "제약", "생명과학", "바이오"),
        "none",
        "바이오·제약은 PER·PBR이 잘 맞지 않아요",
        "아직 이익이 적거나 적자인 회사가 많아서 두 지표 모두 의미가 작아요. "
        "신약 개발 단계, 기술 수출 계약 같은 소식이 주가에 더 큰 영향을 줘요.",
    ),
    Focus(
        (
            "소프트웨어", "인터넷", "양방향미디어", "게임", "엔터테인먼트", "미디어", "광고", "교육",
            "화장품", "식품", "음료", "담배", "섬유", "의류", "호텔", "레저", "백화점", "소매", "판매업체",
        ),
        "per",
        "이 업종은 PER을 주로 봐요",
        "공장 같은 자산보다 브랜드·기술·사람으로 돈을 버는 업종이라, 가진 자산(PBR)보다 버는 돈(PER)을 주로 봐요. "
        "그래서 PBR이 높게 나와도 이상한 일이 아니에요.",
    ),
)

DEFAULT = Focus(
    (),
    "per",
    "보통은 PER을 먼저 봐요",
    "대부분의 업종은 1년 이익에 비해 주가가 어떤지(PER)를 먼저 보고, PBR은 함께 참고해요.",
)

LOSS = Focus(
    (),
    "pbr",
    "적자라서 PBR을 봐요",
    "최근 1년 적자라 PER을 계산할 수 없어요. 이럴 땐 가진 자산에 비해 주가가 어떤지(PBR)와 실적이 나아지고 있는지를 봐요.",
)


def decide(industry_name: str | None, eps: float | None) -> Focus:
    name = (industry_name or "").replace(" ", "")
    for rule in RULES:
        if any(w in name for w in rule.words):
            # 바이오처럼 원래 둘 다 안 맞는 업종은 적자여도 그 설명을 그대로 쓴다
            if eps is not None and eps <= 0 and rule.focus != "none":
                return LOSS
            return rule
    if eps is not None and eps <= 0:
        return LOSS
    return DEFAULT
