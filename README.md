# stock-newbie-stroll (주식초보나들이)

주식 초보가 **차트 · 뉴스 · 증권사 리포트 · 공시**를 한 화면에서 쉽게 훑어볼 수 있게 해 주는 개인용 웹서비스.

이 문서는 프로젝트 소개이자 **대화 이어가기 문서**다. 어떤 환경(다른 PC, 새 Claude 세션)에서든 이 파일과 [CLAUDE.md](CLAUDE.md), [docs/](docs/)만 읽으면 지금까지의 결정과 맥락을 그대로 이어받을 수 있게 유지한다.

- 최종 갱신: 2026-11-12
- 현재 단계: **1단계 + 화면 구성 변경 완료** → 다음은 2단계(뉴스). 남은 일은 docs/decisions.md 맨 아래

---

## 1. 왜 만드는가

- 만드는 사람(= 쓰는 사람)은 **주식 초보**이고, 직업은 Java/Spring 기반 보험시스템 백엔드 개발자다.
- 2023년 SSAFY 팀 프로젝트 [NewStocks/NewStocks](https://github.com/NewStocks/NewStocks)(주식 뉴스 & 오답노트 복기 서비스)에서 백엔드를 맡았다. 그 서비스의 핵심 기능인 **"주식 차트 위에 그날의 뉴스를 띄워 보여주기"** 를 혼자 쓰기 좋은 가벼운 구조로 다시 만든다.
- 여기에 **증권사 애널리스트 리포트를 초보 눈높이로 요약**해서 같이 보여주는 기능을 더한다.
- 자산 현황·투자 방침 같은 개인 금융 기록은 별도 private 레포 `asset-management`에 있다. **이 레포에는 금액·수량 같은 개인 금융정보를 넣지 않는다.**

## 2. 만들 기능

| 기능 | 설명 | 단계 |
|---|---|---|
| 주가 차트 | 국내 주식 일봉 데이터를 매일 수집해 캔들 차트로 표시 | 1 |
| 차트 위 뉴스 | 종목 뉴스를 수집해 차트 날짜에 연결. 날짜를 누르면 그날 뉴스가 뜸. 비슷한 기사 묶기, 긍정/부정 표시 | 2 |
| 리포트 피드 | 매일 나오는 증권사 종목 리포트를 **가급적 전부** 모아 간단 요약과 함께 보여줌 | 3 |
| 초보용 상세 요약 | 관심 종목 리포트와 직접 고른 리포트는 리스크·용어 설명까지 풀어서 요약 | 3 |
| 공시 | OpenDART 공시(실적, 증자, 전환사채 등)를 차트 날짜에 연결 | 4 |
| 매일 자동 실행 | 장 마감 뒤 수집·요약을 자동으로 돌림 | 4 |

### 초보용 요약의 틀

리포트를 통째로 줄이지 않고, 초보가 꼭 봐야 할 부분만 같은 틀로 뽑는다.

```
📄 종목 | 증권사 | 날짜
한 줄 결론
투자의견 / 목표주가 (이전 대비 상향·하향)   └ 용어 풀이 한 줄
핵심 근거 3가지
조심할 점 (리스크)
처음 보는 용어 → 쉬운 설명
이전 리포트와 달라진 점
원문 링크
```

- **간단 요약**(전체 리포트): 한 줄 결론, 투자의견, 목표주가 변화, 핵심 근거 3가지. 리포트 첫 1~2페이지만 사용.
- **상세 요약**(관심 종목 + 직접 누른 리포트): 위 틀 전부.
- 한 번 만든 요약은 DB에 저장해 다시 만들지 않는다.
- 요약은 리포트 내용을 **전달**하는 데까지만 한다. "사라/팔아라" 같은 판단은 넣지 않는다.

## 3. 원칙 (바꾸려면 사용자와 다시 상의)

1. **추가 요금 없이 만든다.**
   - 데이터는 무료 출처만 쓴다 (아래 5번 표).
   - 서버는 클라우드가 아니라 사용자 PC에서 돌린다.
   - 리포트 요약에 유료 LLM API를 붙이지 않는다. 사용자가 이미 쓰는 Claude 구독 안에서 **Claude Code 예약 작업**이 새 리포트를 읽고 요약을 DB에 써 넣는 방식을 기본으로 한다. (3단계에서 구체화. 대안: 무료 등급 API, 로컬 모델)
2. **백엔드는 사용자가 이해할 수 있어야 한다.**
   - FastAPI를 쓰되 폴더·계층은 Spring처럼 나눈다 (router = Controller, service, repository, models = Entity, schemas = DTO).
   - 백엔드 파일에는 "Spring의 무엇에 해당하는지"를 주석으로 단다.
   - 기능을 하나 붙일 때마다 요청 흐름을 Spring 기준으로 설명한다. 자세한 대응표는 [docs/spring-to-fastapi.md](docs/spring-to-fastapi.md).
3. **프론트엔드는 Claude가 맡는다.** 사용자는 프론트 코드를 깊이 이해하지 않아도 된다. 대신 구조를 단순하게 유지한다.
4. **비밀값은 코드에 쓰지 않는다.** API 키 등은 `.env`에만 두고 커밋하지 않는다. (NewStocks 공개 레포에 DB 비밀번호가 하드코딩돼 있던 일을 반복하지 않는다.)
5. **저작권**: 증권사 리포트 PDF 원문은 레포에 올리지 않고, 앱을 남에게 공개할 경우 요약과 원문 링크만 보여준다. 지금은 개인용이다.
6. **크롤링보다 공식 API 우선.** 크롤링은 사이트 구조가 바뀌면 깨진다.

## 4. 구성

```
stock-newbie-stroll/
  backend/     FastAPI + SQLAlchemy + SQLite (JSON API만 담당, 포트 8100)
  frontend/    Next.js + TypeScript + TradingView Lightweight Charts (화면, 포트 3000)
  docs/        결정 기록, Spring↔FastAPI 대응표
  README.md    이 문서 (대화 이어가기)
  CLAUDE.md    Claude Code가 이 폴더에서 시작할 때 읽는 안내
```

### 백엔드 폴더 규칙 (Spring식 계층)

```
backend/app/
  main.py            ← @SpringBootApplication (앱 시작점, 라우터 등록)
  core/
    config.py        ← application.yml (.env 읽기)
    database.py      ← DataSource / EntityManager 설정
  stock/             ← 도메인 패키지 (NewStocks의 stock 패키지와 같은 모양)
    router.py        ← Controller
    service.py       ← Service
    repository.py    ← Repository
    models.py        ← Entity
    schemas.py       ← DTO
    collector.py     ← 외부 데이터 수집 (NewStocks의 파이썬 pykrx 서버 역할)
```

도메인이 늘면 `news/`, `report/`, `disclosure/`를 같은 모양으로 추가한다.

### 왜 이 구성인가 (결정 요약)

| 결정 | 이유 |
|---|---|
| NewStocks를 그대로 띄우지 않고 새로 만듦 | 서버 5개·언어 3개(Spring, Next.js, Flask×3, MySQL) 구조라 혼자 관리하기 무겁고, 설정(.env)·운영 DB가 없으며 라이브러리가 낡음 |
| Spring 대신 FastAPI | pykrx·크롤링·요약이 모두 Python이라 서버 하나로 합칠 수 있음. Spring 계층 구조를 그대로 흉내 낼 수 있음 |
| Django가 아닌 FastAPI | 숨은 관례가 적어 흐름이 코드에 그대로 보임. 관리자 페이지·회원 기능이 필요 없음 |
| MySQL 대신 SQLite | 혼자 쓰는 도구라 파일 하나로 충분. 설치 불필요 |
| 화면은 처음부터 Next.js | 리포트 피드·필터·차트 연동 등 화면이 앱 수준으로 커질 것이라, 나중에 옮기는 비용이 더 큼 |
| 로그인·커뮤니티·오답노트 제외 | 혼자 쓰는 도구. 필요해지면 나중에 추가 |
| 코드 레포와 자산 기록 레포 분리 | 개인 금융정보 보호, 커밋 기록·Claude 맥락 분리 |

전체 결정 기록은 [docs/decisions.md](docs/decisions.md).

## 5. 데이터 출처 (전부 무료)

| 데이터 | 출처 | 비고 |
|---|---|---|
| 주가(일봉) | pykrx (대안: FinanceDataReader) | pykrx가 실패하면 자동으로 FinanceDataReader로 재시도. pykrx가 "KRX 로그인 실패" 경고를 찍지만 일봉 조회는 동작함 (2026-11-11 확인) |
| 뉴스 | 네이버 검색 API(공식·무료, 키 발급 필요) 우선, 네이버 금융 종목 뉴스 | 2단계 |
| 증권사 리포트 | 네이버 금융 리서치 > 종목분석 | 3단계. 하루 수십 건 수준 |
| 공시 | OpenDART API(공식·무료, 키 발급 필요) | 4단계 |

## 6. 관심 종목 (뉴스·상세 요약 대상)

| 종목 | 코드 |
|---|---|
| 삼성전자 | 005930 |
| SK하이닉스 | 000660 |
| 두산 | 000150 |
| 펨트론 | 168360 |

- 뉴스와 상세 요약은 관심 종목만, **리포트 간단 요약은 전체 종목**을 대상으로 한다.
- 참고: ETF는 증권사 리포트가 거의 없고, 소형주(펨트론)는 리포트가 드물어 공시·뉴스가 더 중요하다.

## 7. 단계별 계획과 진행 상황

- [x] **1단계** — FastAPI 뼈대(SQLite), 관심 종목 일봉 수집, Next.js 캔들 차트 화면 (2026-11-11 구현. 사용자가 직접 띄워 보고 흐름 설명을 듣는 일이 남음)
- [ ] **2단계** — 뉴스 수집, 차트 날짜와 연결, 중복 묶기·긍정/부정 표시
- [ ] **3단계** — 증권사 리포트 수집, 간단 요약(전체) + 초보용 상세 요약(관심 종목), 리포트 피드 화면
- [ ] **4단계** — OpenDART 공시, 매일 자동 실행(장 마감 뒤)

단계가 끝날 때마다: 사용자가 직접 띄워 보고 → Claude가 요청 흐름을 Spring 기준으로 설명 → 이 표와 [docs/decisions.md](docs/decisions.md) 갱신 → 커밋.

## 8. 실행 방법

필요한 것: Python 3.12, Node.js 22

한 번에 띄우기 (설치를 마친 뒤): 레포 폴더에서 `dev.cmd` 실행 → http://localhost:3000

백엔드 포트가 8100인 이유: 이 PC에서 8000번은 다른 프로젝트(SMPortal, Django)가 쓰고 있다.

```bash
# 백엔드 (처음 한 번)
cd backend
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 백엔드 실행 → http://localhost:8100/docs 에서 API 문서(Swagger) 확인
.venv\Scripts\uvicorn app.main:app --reload --port 8100
```

```bash
# 프론트엔드 (처음 한 번)
cd frontend
npm install

# 프론트엔드 실행 → http://localhost:3000
npm run dev
```

```bash
# 주가 수집 (관심 종목, 마지막 저장일 다음 날부터 오늘까지)
cd backend
.venv\Scripts\python -m app.stock.collector
```

수집은 `POST http://localhost:8100/stocks/collect` 로도 실행할 수 있다. 4단계에서 매일 자동 실행으로 바꾼다.

## 9. 알려진 제약

- 수집·자동 실행은 이 PC가 켜져 있을 때만 돈다.
- pykrx와 크롤링은 대상 사이트가 바뀌면 고쳐야 한다.
- 개발 PC는 Windows 11이다. 명령 예시는 Windows 기준.

## 10. 대화를 이어가는 방법

- **Claude Code**: 이 폴더에서 세션을 시작하면 [CLAUDE.md](CLAUDE.md)를 따라 이 README와 docs를 먼저 읽고 이어간다.
- **Claude 앱(웹·모바일)**: 이 README 내용을 붙여 넣거나 첨부하고 시작한다.
- 결정이 바뀌거나 단계가 끝나면 README(7번 진행 상황, 최종 갱신일)와 [docs/decisions.md](docs/decisions.md)를 같이 고친다.

## 11. 아직 정하지 않은 것 / 남은 일

- 3단계 요약 방식 구체화 (Claude Code 예약 작업으로 요약을 DB에 넣는 흐름, 실행 시각)
- 네이버 검색 API, OpenDART API 키 발급 (사용자가 직접 발급해 `.env`에 입력)
- 매일 자동 실행 시각 (장 마감 뒤, 예: 저녁 7시)
- 별개 작업: NewStocks 공개 레포에 남아 있는 DB 비밀번호 정리 (같은 비밀번호를 쓰는 곳이 있으면 변경)
