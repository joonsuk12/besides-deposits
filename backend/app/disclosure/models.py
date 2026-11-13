"""Entity. Spring의 @Entity 클래스에 해당한다."""
from datetime import date

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DartCorp(Base):
    """종목코드 ↔ DART 고유번호 대응표.

    DART는 회사를 종목코드(005930)가 아니라 자기 고유번호(00126380)로 구분한다.
    OpenDART가 주는 전체 회사 목록 파일을 처음 한 번 받아 저장해 둔다.
    """

    __tablename__ = "dart_corp"

    stock_code: Mapped[str] = mapped_column(primary_key=True)  # 005930
    corp_code: Mapped[str] = mapped_column(index=True)  # 00126380
    corp_name: Mapped[str]


class Disclosure(Base):
    """공시 한 건 (DART 공시 목록의 한 줄)."""

    __tablename__ = "disclosure"

    rcept_no: Mapped[str] = mapped_column(primary_key=True)  # 접수번호 (원문 주소에 쓰임)
    stock_code: Mapped[str] = mapped_column(index=True)
    corp_name: Mapped[str]
    report_nm: Mapped[str]  # 보고서 이름 (예: "주요사항보고서(유상증자결정)")
    filer: Mapped[str]  # 제출인 (회사 자신 또는 대주주·증권사 등)
    rcept_dt: Mapped[date] = mapped_column(index=True)  # 접수일
    remark: Mapped[str] = mapped_column(default="")  # 비고 (유: 유가증권시장 소관, 정: 정정 있음 등)
