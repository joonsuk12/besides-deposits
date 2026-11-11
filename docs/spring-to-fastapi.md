# Spring ↔ FastAPI 대응표

이 프로젝트의 백엔드를 Spring 기준으로 읽기 위한 안내.

| Spring | 이 프로젝트 (FastAPI) | 비고 |
|---|---|---|
| `@SpringBootApplication` | `app/main.py`의 `app = FastAPI()` | 라우터 등록도 여기서 |
| `application.yml` | `.env` + `app/core/config.py` | |
| DataSource, `EntityManager` | `app/core/database.py`의 `engine`, `Session` | |
| `@RestController` + `@GetMapping` | `router.py`의 `@router.get(...)` | |
| `@PathVariable`, `@RequestParam` | 함수 인자 (타입 힌트로 구분) | |
| DTO + `@Valid` | `schemas.py`의 Pydantic 모델 | 타입만 적으면 검증 자동 |
| `@Service` | `service.py`의 함수 | 어노테이션 없음 |
| `@Repository` + JPA | `repository.py` + SQLAlchemy | |
| `@Entity` | `models.py`의 SQLAlchemy 모델 | |
| `@Autowired` / 생성자 주입 | `Depends(get_db)` | 함수 인자로 주입 |
| `@Transactional` | `db.commit()` 직접 호출 | 요청마다 세션 하나 |
| `ddl-auto: update` | `Base.metadata.create_all()` | 없는 테이블만 생성 |
| `@Scheduled` | APScheduler (4단계) | |
| Swagger (springdoc) | `/docs` 자동 제공 | 설정 불필요 |

## 요청 하나가 지나가는 길

`GET /stocks/005930/prices` 를 예로 들면:

1. `stock/router.py` — URL을 받아 인자를 꺼낸다 (Controller)
2. `stock/service.py` — 종목이 있는지 확인하고 필요한 데이터를 모은다 (Service)
3. `stock/repository.py` — DB에서 조회한다 (Repository)
4. `stock/models.py` — 조회 결과가 담기는 객체 (Entity)
5. `stock/schemas.py` — 응답 JSON 모양으로 바꾼다 (DTO)
