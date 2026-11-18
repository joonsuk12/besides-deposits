"""Entity. Spring의 @Entity 클래스에 해당한다.

마이데이터: 사용자가 화면의 질문에 답한 기록을 모은다 (위험 신호를 보고 든 생각, 관심을 둔 이유, 타임머신 연습 답 등).
나중에 "나는 어떤 신호를 보면 걱정하나", "내 예상은 얼마나 맞았나"처럼 가공하려고, 답과 함께 그때의 상황(주가 등)을 남긴다.

- 보유 수량·금액 같은 개인 금융정보는 넣지 않는다 (그건 별도 레포 asset-management).
- 질문 종류가 늘어도 테이블을 새로 만들지 않도록 kind로 구분하고, 종류마다 다른 정보는 context_json에 둔다.
"""
from datetime import datetime

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MyRecord(Base):
    __tablename__ = "my_record"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(index=True)  # risk_reaction / watch_reason / timemachine_guess …
    stock_code: Mapped[str | None] = mapped_column(index=True)
    question: Mapped[str]  # 화면에 보여준 질문 그대로 (질문 문구가 바뀌어도 그때 무엇을 물었는지 남게)
    answer: Mapped[str]  # 고른 답 (예: "worried")
    answer_label: Mapped[str]  # 고른 답의 화면 글자 (예: "걱정돼요")
    memo: Mapped[str] = mapped_column(Text, default="")  # 직접 쓴 한 줄
    context_json: Mapped[str] = mapped_column(Text, default="{}")  # 답할 때의 상황 (주가, 신호 개수 등)
    created_at: Mapped[datetime] = mapped_column(index=True)
