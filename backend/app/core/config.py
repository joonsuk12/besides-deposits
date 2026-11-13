"""설정. Spring의 application.yml에 해당한다.

값은 backend/.env 파일이나 환경변수에서 읽고, 없으면 아래 기본값을 쓴다.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = f"sqlite:///{(DATA_DIR / 'stroll.db').as_posix()}"
    # 프론트엔드(Next.js) 주소. 여기 적힌 곳에서 오는 요청만 허용한다 (CORS).
    cors_origins: list[str] = ["http://localhost:3000"]
    # OpenDART 인증키 (https://opendart.fss.or.kr, 무료). .env의 DART_API_KEY. 없으면 공시 기능만 꺼진다.
    dart_api_key: str | None = None


settings = Settings()
