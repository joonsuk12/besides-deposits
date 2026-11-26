# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

주식 초보용 개인 웹서비스 "비사이드디포짓(BESIDES DEPOSITS)" (2026-11-16 이전 이름: 주식초보나들이). GitHub 레포는 `joonsuk12/besides-deposits`, 이 PC의 폴더 이름은 그대로 `stock-newbie-stroll`. 대화를 시작하면 먼저 `docs/PROJECT.md`(작업용 문서, 예전 README)와 `docs/decisions.md`를 읽고 그 결정들을 전제로 이어간다.

## 사용자

- Java/Spring 백엔드 개발자, 주식 초보. 한국어로 대화한다.
- **백엔드 구조를 직접 이해하고 싶어 한다.** 백엔드 코드를 추가하면 요청 흐름을 Spring 기준으로 설명한다.
- 프론트엔드는 깊이 이해하지 않아도 된다고 했다. 프론트는 단순하게 유지하고 설명은 짧게 한다.
- 승인이나 의견이 필요하면 PC 푸시 알림으로 알린다.
- 서버를 (재)기동하면 답변 마지막에 확인용 URL 목록을 준다.

## 지켜야 할 원칙

- **추가 요금 금지**: 유료 API, 유료 클라우드를 붙이지 않는다 (Claude API 같은 유료 AI 호출 포함). 비용이 생기는 선택지는 먼저 사용자에게 묻는다.
- **백엔드 계층**: 도메인별 폴더에 `router.py`(Controller) / `service.py` / `repository.py` / `models.py`(Entity) / `schemas.py`(DTO), 외부 호출은 `client.py`. router는 service만, service는 repository(다른 도메인 것 포함)만 호출한다. 새 파일 첫머리에 Spring 대응 주석을 단다.
- **비밀값**: `.env`에만 둔다. 코드·커밋·문서에 쓰지 않는다. `.env.example`에 이름만 적는다.
- **개인 금융정보**(보유 수량, 금액)는 이 레포에 넣지 않는다. 그 기록은 별도 레포 `asset-management`에 있다. 마이데이터(`mydata`)에도 넣지 않는다.
- 증권사 리포트 PDF 원문, SQLite DB 파일은 커밋하지 않는다.
- 화면 문구·요약에 매수·매도 권유를 넣지 않는다. 원인·좋고 나쁨을 단정하지 않고 "같은 날 있었던 일", "확인할 것"으로 쓴다.
- **프론트 CSS는 `frontend/src/app/globals.css`의 디자인 토큰(`--fs-*`, `--r-*`, 색 변수)만 쓴다.** 새 숫자·색이 필요하면 토큰을 먼저 늘린다.
- 버튼·칩·카드·더보기는 `frontend/src/app/ui.css`의 공통 클래스(`ui-btn`, `ui-btn-ghost`, `ui-chip`, `ui-card`, `ui-more`)를 쓴다. 서비스 이름은 `frontend/src/lib/brand.ts`.
- 결정이 바뀌거나 단계가 끝나면 `docs/PROJECT.md`(7번 진행 상황, 최종 갱신일)와 `docs/decisions.md`(날짜별 결정 + 맨 아래 "지금 상태와 남은 일")를 갱신한다.

## Git 작업 방식

- **새 작업은 main에서 새 브랜치를 만들어 시작한다** (2026-11-12 사용자 요청). 이름 예: `feature/disclosure`, `fix/report-headline`.
- 작업이 끝나면 그 브랜치에 커밋·push하고, main에 합칠지는 사용자에게 묻는다 (합칠 때는 `--no-ff` merge 후 push).
- main에 직접 커밋하지 않는다 (문서 오타 같은 아주 작은 수정도 사용자에게 먼저 확인).

## 실행·확인 명령 (Windows)

- 한 번에: 레포 루트에서 `dev.cmd` (백엔드 새 창 + 프론트)
- 백엔드: `backend`에서 `.venv\Scripts\uvicorn app.main:app --reload --port 8100` (Python 3.12, API 문서 http://localhost:8100/docs). 8000번은 이 PC의 다른 프로젝트가 쓴다.
- 프론트: `frontend`에서 `npm run dev` (Node 22, 포트 3000). PowerShell에서는 `npm`이 막혀 있어 `npm.cmd run dev`, `npx.cmd`를 쓴다.
- 주가 수집: `backend`에서 `.venv\Scripts\python -m app.stock.collector`
- 매일 수집(작업 스케줄러가 평일 18:00에 `daily_collect.cmd` → `python -m app.daily`, 로그 `backend\data\daily.log`)
- 리포트 "쉽게 말하면" 요약: 예약 작업이 `python -m app.report.easy_cli pending|save ...`로 서버 없이 DB를 읽고 쓴다.
- 테스트 스위트와 lint 스크립트는 없다. 확인은 프론트 `npx.cmd tsc --noEmit -p .`, 백엔드는 API를 직접 호출해 보고, 화면은 브라우저로 본다.
- `.env`를 고친 뒤에는 백엔드를 재시작해야 반영된다 (`--reload`는 `.env` 변경을 감지하지 않음). `.env`는 보안 훅 때문에 셸로 읽거나 고칠 수 없으니, 값 확인이 필요하면 `app.core.config.settings`를 통해 (값은 출력하지 않고) 확인한다.

## 구조 (여러 파일을 봐야 알 수 있는 것)

**백엔드** (`backend/app`, FastAPI + SQLAlchemy 2 + SQLite `backend/data/stroll.db`)
- 도메인: `stock`(종목·주가·관심종목) `report`(증권사 리포트) `news` `disclosure`(OpenDART 공시) `valuation`(PER·PBR·연간 재무) `trend`(투자자별 매매) `etf` `risk`(위험 신호, 테이블 없이 다른 도메인 조합) `mydata`(화면 질문에 대한 사용자 답 기록) `quiz`(오늘의 읽기 퀴즈, 테이블 없이 다른 도메인 규칙으로 문제·정답을 만들고 답은 mydata에) `practice`(예전 타임머신 — 화면은 `/quiz`로 바뀌었고 계산·기록용으로 남음, 시장 데이터: 지수 `index_price`, KRX 업종 PER·PBR `index_valuation`, 국고채 금리 `bond_yield`, 종목→업종 `krx_sector_member`).
- 새 도메인을 만들면 두 곳에 등록한다: `app/main.py`의 `include_router`, `app/core/database.py`의 `create_tables()` 안 models import (테이블은 서버 시작 때 없는 것만 만들고, 컬럼 변경은 반영되지 않는다).
- **외부 데이터는 "조회 시점 수집 + 캐시" 패턴**: service가 `core/fetch_log.is_fresh(db, key, 분)`으로 신선도를 보고, 오래됐으면 client로 받아 `db.merge`로 저장한 뒤 `mark_fetched`. 외부 실패는 try/except로 삼키고 저장된 데이터로 응답한다 (화면이 깨지지 않게). 응답 모양이 자주 바뀌는 외부 JSON은 `raw_json` 컬럼에 통째로 두고 service에서 화면용으로 바꾼다.
- 외부 출처 (모두 무료): 네이버 증권 내부 API(`core/naver.get_json`, 요청 간격 0.5초, 일부는 `MOBILE_BASE_URL`), OpenDART(`DART_API_KEY`), pykrx(KRX 로그인 필요 → `core/krx.use_login()`이 `.env`의 `KRX_ID`·`KRX_PW`를 환경 변수로 넘긴 다음 import해야 한다). **KRX는 요청이 몰리면 IP를 막는다**(2026-11-24 실제로 막힘) — 그래서 **KRX는 ETF 구성종목 비중에만** 쓴다(주가는 FinanceDataReader, 타임머신 업종·금리는 저장된 값만, `KRX_MARKET_DATA = False`). 실패하면 `core/krx.pause()`로 60분 쉬고, 테스트할 때도 KRX를 반복 호출하지 않는다, FinanceDataReader(종목 목록·지수·주가 대안), ETF 운용사 홈페이지(TIME).
- 초보용 분류는 유료 AI 없이 규칙으로: 공시는 `disclosure/keypoints.py`의 `RULES`(위에서부터 첫 일치, `category`·`level`), 리포트는 `report/keypoints.py`. 위험 신호도 이 분류 결과를 재사용한다.

**프론트** (`frontend/src`, Next.js 16 App Router + React 19, 전부 client component + CSS Modules)
- 화면: `/` 홈(관심종목 오늘 소식), `/[code]` 종목 차트 화면(중심), `/quiz` 오늘의 읽기 퀴즈(`/practice`는 여기로 보냄), `/mydata` 내 기록(마이데이터 가공), `/watchlist`, `/reports`, `/guide`, `/intro`.
- 백엔드 호출과 타입은 모두 `lib/api.ts` 한 파일 (`NEXT_PUBLIC_API_URL`, 기본 `http://localhost:8100`).
- 차트는 `components/StockChart.tsx`(lightweight-charts 5, 일→주→월→연봉 자동 전환, 마커 N/R/D와 타임머신 `cutDate`, 지표 계산은 `lib/indicators.ts`). TradingView 로고는 끄고 출처 링크를 따로 둔다(라이선스 조건).
- 종목 화면은 ETF(`stock.market === "ETF"`)면 회사용 카드(PER·위험 신호·공시·리포트) 대신 `EtfCard`를 보여준다.
