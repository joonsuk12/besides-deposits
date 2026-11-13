"""앱 시작점. Spring의 @SpringBootApplication 클래스에 해당한다.

실행: uvicorn app.main:app --reload --port 8100
API 문서(Swagger): http://localhost:8100/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal, create_tables
from app.stock import service as stock_service
from app.disclosure.router import router as disclosure_router
from app.news.router import router as news_router
from app.report.router import router as report_router
from app.stock.router import router as stock_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 뜰 때 한 번 실행된다 (@PostConstruct / ApplicationRunner와 비슷).
    create_tables()
    with SessionLocal() as db:
        stock_service.init_stock_data(db)
    yield


app = FastAPI(title="주식초보나들이 API", lifespan=lifespan)

# 프론트엔드(다른 포트)에서 오는 요청을 허용한다. Spring의 CORS 설정(WebMvcConfigurer)과 같다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 도메인별 Controller 등록. 도메인이 늘면 여기에 한 줄씩 추가한다.
app.include_router(stock_router)
app.include_router(report_router)
app.include_router(news_router)
app.include_router(disclosure_router)
