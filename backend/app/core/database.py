"""DB 연결. Spring의 DataSource / EntityManager 설정에 해당한다.

- engine       : DataSource (DB 연결 풀)
- SessionLocal : EntityManager를 만들어 주는 공장
- Base         : 모든 Entity의 부모 클래스
- get_db       : 요청 하나마다 세션을 열고 닫아 주는 함수. router에서 Depends(get_db)로 주입받는다.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import DATA_DIR, settings

DATA_DIR.mkdir(exist_ok=True)

engine = create_engine(
    settings.database_url,
    # SQLite는 기본적으로 한 스레드에서만 쓰게 막혀 있어서 풀어 준다.
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """없는 테이블만 만든다. JPA의 ddl-auto: update와 비슷하다 (컬럼 변경은 반영하지 않음)."""
    # Entity를 Base에 등록하기 위한 import. 도메인이 늘면 여기에 추가한다.
    from app.core import fetch_log  # noqa: F401
    from app.disclosure import models as disclosure_models  # noqa: F401
    from app.news import models as news_models  # noqa: F401
    from app.report import models as report_models  # noqa: F401
    from app.stock import models as stock_models  # noqa: F401

    Base.metadata.create_all(engine)
