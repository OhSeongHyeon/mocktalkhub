# News Bot Work Plan

## 1. 작업 원칙

- 최소 백오피스 화면과 백엔드, 문서를 함께 묶어 MVP를 만든다.
- 새 기능은 기존 `board`, `article`, `article_category`, `admin audit log` 구조를 최대한 재사용한다.
- 외부 API 호출과 스케줄링은 장애 전파를 최소화하도록 느슨하게 결합한다.

현재 상태:

- Phase 1 ~ Phase 7 기준 MVP 구현과 기본 운영 검증이 완료된 상태다.

## 2. 단계별 계획

## Phase 1. 요구사항 확정 및 문서화 `[완료]`

산출물:

- `requirements.md`
- `design.md`
- `functional-spec.md`
- `work-plan.md`

완료 기준:

- 새 테이블 필요성, 봇 사용자 필요성, 스케줄 방식이 문서에서 합의된다.

## Phase 2. DB 스키마 추가 `[완료]`

예상 작업:

- Flyway migration 추가
- `tb_news_collection_jobs`
- `tb_news_collected_items`
- 필요한 인덱스 및 유니크 제약 추가

완료 기준:

- 잡 설정과 dedupe 상태를 DB에 저장할 수 있다.

## Phase 3. 도메인 모델 및 관리자 API `[완료]`

예상 작업:

- entity / repository / dto 작성
- 관리자 목록/생성/수정/on-off/run now API 작성
- on/off / run now / 목록 조회 구현
- 관리자 audit log 연동

완료 기준:

- Swagger와 백오피스에서 잡 생성/수정/비활성화/즉시 실행이 가능하다.

## Phase 4. 외부 소스 어댑터 구현 `[완료]`

예상 작업:

- `HackerNewsSourceClient`
- `DevToSourceClient`
- `GitHubReleasesSourceClient`
- `RssSourceClient`

완료 기준:

- 각 소스에서 공통 `NewsBotSourceItem` 목록을 돌려줄 수 있다.

## Phase 5. 게시판/카테고리/게시글 발행 구현 `[완료]`

예상 작업:

- 시스템 계정 `news_bot` 보장 생성 전략 구현
- 게시판 자동 생성 서비스 구현
- 카테고리 자동 생성 서비스 구현
- 내부 게시글 발행 서비스 구현
- 동일 항목 update 전략 구현

완료 기준:

- 외부 항목이 실제 `tb_articles`에 적재되고, 작성자는 `news_bot`으로 고정된다.

## Phase 6. 스케줄러 구현 `[완료]`

예상 작업:

- dispatcher poller 추가
- due job 조회
- 잡 선점 처리
- next_run_at 갱신
- 실패 상태 기록
- 수동 실행과 자동 실행 중복 방지

완료 기준:

- 운영자가 등록한 interval 기준으로 주기 수집이 동작한다.

## Phase 7. 테스트 및 운영 검증 `[진행 후 1차 완료]`

예상 작업:

- 어댑터 fixture 테스트
- job service 단위 테스트
- scheduler 동작 테스트
- article publish 통합 테스트
- 중복 방지 테스트

완료 기준:

- 핵심 정상/오류 시나리오가 테스트로 고정된다.

## 3. 권장 구현 순서

1. Flyway + entity + repository
2. 관리자 API
3. GitHub Releases 어댑터
4. RSS 어댑터
5. Hacker News 어댑터
6. DEV 어댑터
7. 스케줄러
8. 테스트 보강

이 순서를 권장하는 이유:

- GitHub Releases와 RSS가 게시판 적재 품질이 가장 높다.
- Hacker News와 DEV는 이후 추가해도 구조 변경이 적다.
- 관리자 API와 DB 모델이 먼저 고정돼야 나머지 구현이 흔들리지 않는다.

## 4. 리스크와 대응

### 리스크 1. GitHub 무인증 rate limit

- 내용: 공개 API라도 무인증 호출은 시간당 한도가 낮다.
- 대응: repo 수를 제한하고 기본 수집 주기를 길게 잡는다.

### 리스크 2. RSS/Atom 포맷 편차

- 내용: source마다 XML 구조가 조금씩 다르다.
- 대응: MVP는 검증된 allowlist feed만 등록한다.

### 리스크 3. 중복 게시글

- 내용: 같은 기사가 소스별로 중복 유입될 수 있다.
- 대응: 1차는 job 단위 dedupe, 2차는 추후 URL canonicalization 확장 검토

### 리스크 4. 게시판 자동 생성 남발

- 내용: 잘못된 잡 설정이 많으면 게시판이 과도하게 생성될 수 있다.
- 대응: 자동 생성은 기본 off 또는 관리자 전용 기능으로 제한

### 리스크 5. 장기 실행 트랜잭션

- 내용: 외부 호출을 트랜잭션 안에서 처리하면 락과 타임아웃 위험이 커진다.
- 대응: 외부 호출과 DB 쓰기 단계를 분리한다.

## 5. 테스트 전략

- 단위 테스트:
- due job 선택
- next_run_at 계산
- dedupe/update 판정
- 소스별 응답 파싱

- 통합 테스트:
- 게시판 자동 생성
- 카테고리 자동 생성
- 게시글 생성
- 동일 external key 재수집

- 비목표:
- CI에서 실시간 외부 API 호출 테스트

실시간 외부 API 테스트는 flaky하므로 fixture 기반으로 대체한다.

## 6. 실제 작업 단위 예시

- `docs: 뉴스봇 요구사항 및 설계 문서 추가`
- `feat: 뉴스봇 잡 스키마 추가`
- `feat: 뉴스봇 관리자 API 추가`
- `feat: GitHub Releases 및 RSS 수집 어댑터 추가`
- `feat: 뉴스봇 스케줄러 및 게시글 발행 구현`
- `test: 뉴스봇 수집 및 중복 방지 테스트 추가`
