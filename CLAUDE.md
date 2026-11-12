# CLAUDE.md

주식 초보용 개인 웹서비스 "주식초보나들이". 대화를 시작하면 먼저 `README.md`와 `docs/decisions.md`를 읽고 그 결정들을 전제로 이어간다.

## 사용자

- Java/Spring 백엔드 개발자, 주식 초보. 한국어로 대화한다.
- **백엔드 구조를 직접 이해하고 싶어 한다.** 백엔드 코드를 추가하면 요청 흐름을 Spring 기준으로 설명한다.
- 프론트엔드는 깊이 이해하지 않아도 된다고 했다. 프론트는 단순하게 유지하고 설명은 짧게 한다.
- 승인이나 의견이 필요하면 PC 푸시 알림으로 알린다.

## 지켜야 할 원칙

- **추가 요금 금지**: 유료 API, 유료 클라우드를 붙이지 않는다. 비용이 생기는 선택지는 먼저 사용자에게 묻는다.
- **백엔드 계층**: 도메인별 폴더에 `router.py`(Controller) / `service.py` / `repository.py` / `models.py`(Entity) / `schemas.py`(DTO). router는 service만, service는 repository만 호출한다. 새 파일 첫머리에 Spring 대응 주석을 단다.
- **비밀값**: `.env`에만 둔다. 코드·커밋·문서에 쓰지 않는다. `.env.example`에 이름만 적는다.
- **개인 금융정보**(보유 수량, 금액)는 이 레포에 넣지 않는다. 그 기록은 별도 레포 `asset-management`에 있다.
- 증권사 리포트 PDF 원문, SQLite DB 파일은 커밋하지 않는다.
- 요약 문구에 매수·매도 권유를 넣지 않는다.
- 결정이 바뀌거나 단계가 끝나면 `README.md`(진행 상황, 최종 갱신일)와 `docs/decisions.md`를 갱신한다.

## Git 작업 방식

- **새 작업은 main에서 새 브랜치를 만들어 시작한다** (2026-11-12 사용자 요청). 이름 예: `feature/disclosure`, `fix/report-headline`.
- 작업이 끝나면 그 브랜치에 커밋·push하고, main에 합칠지는 사용자에게 묻는다.
- main에 직접 커밋하지 않는다 (문서 오타 같은 아주 작은 수정도 사용자에게 먼저 확인).

## 실행

- 백엔드: `backend`에서 `.venv\Scripts\uvicorn app.main:app --reload --port 8100` (Python 3.12)
- 프론트: `frontend`에서 `npm run dev` (Node 22, 포트 3000)
- 주가 수집: `backend`에서 `.venv\Scripts\python -m app.stock.collector`
