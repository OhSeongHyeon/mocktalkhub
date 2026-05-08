# News Bot Table Spec

## 1. 문서 목적

이 문서는 `news-bot` 기능에 필요한 신규 테이블의 정의를 고정하기 위한 테이블 정의서다.

정리 기준은 아래와 같다.

- `admin`은 백오피스에서 뉴스봇 잡을 생성/수정/실행하는 제어자다.
- `news_bot`은 실제 뉴스 게시글을 작성하는 시스템 계정이다.
- 신규 테이블은 단순 실행 이력 저장만을 위한 것이 아니라, 운영 제어와 중복 방지, 게시글 동기화 보조를 위한 실사용 데이터까지 포함한다.

## 2. 설계 원칙

### 2.1 역할 분리

- `admin`
  - 뉴스봇 잡 생성/수정/비활성화/즉시 실행 담당
  - 백오피스 제어자
- `news_bot`
  - 실제 뉴스 게시글 작성자
  - 일반 회원가입 계정이 아닌 시스템 계정

### 2.2 데이터 범위

- `tb_news_collection_jobs`
  - 운영 제어 테이블
  - 잡 설정과 마지막 실행 상태 저장
- `tb_news_collected_items`
  - 중복 방지 및 동기화 보조 테이블
  - 외부 항목과 내부 게시글 연결 상태 저장

### 2.3 비범위

- 실행 단위 상세 이력 테이블은 MVP 범위에 포함하지 않는다.
- 상세 이력이 필요해지면 추후 `tb_news_job_executions`, `tb_news_job_execution_items` 같은 별도 테이블을 추가한다.

## 3. 테이블 목록

- `tb_news_collection_jobs`
- `tb_news_collected_items`

## 4. `tb_news_collection_jobs`

### 4.1 용도

이 테이블은 뉴스 수집 잡의 설정과 최신 상태를 저장한다.

이 테이블이 담당하는 역할은 아래와 같다.

- 백오피스 on/off 제어
- 수집 주기 관리
- 대상 게시판/카테고리 관리
- 제어자(`admin`)와 작성자(`news_bot`) 분리
- 마지막 실행 상태와 오류 메시지 저장

즉, 이 테이블은 `실행 이력 전용`이 아니라 `운영 제어용`이 핵심이다.

### 4.2 컬럼 정의

| 컬럼명 | 타입 | NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `news_job_id` | `BIGINT` | `NOT NULL` | `GENERATED ALWAYS AS IDENTITY` | 뉴스봇 잡 PK |
| `job_name` | `VARCHAR(120)` | `NOT NULL` |  | 운영자가 식별하는 잡 이름 |
| `source_type` | `VARCHAR(32)` | `NOT NULL` |  | 수집 소스 유형(`HACKER_NEWS`, `DEV_TO`, `GITHUB_RELEASES`, `RSS`) |
| `source_config_json` | `TEXT` | `NOT NULL` |  | 소스별 설정 JSON 문자열 |
| `target_board_slug` | `VARCHAR(80)` | `NOT NULL` |  | 대상 게시판 slug |
| `target_board_name` | `VARCHAR(255)` | `NULL` |  | 자동 생성 시 사용할 게시판명 |
| `target_category_name` | `VARCHAR(48)` | `NULL` |  | 대상 기본 카테고리명 |
| `author_user_id` | `BIGINT` | `NOT NULL` |  | 실제 게시글 작성자. MVP에서는 `news_bot`의 `user_id`를 저장 |
| `created_by_user_id` | `BIGINT` | `NOT NULL` |  | 잡 생성 관리자. 일반적으로 `admin` |
| `updated_by_user_id` | `BIGINT` | `NOT NULL` |  | 마지막 수정 관리자 |
| `is_enabled` | `BOOLEAN` | `NOT NULL` | `TRUE` | 잡 활성화 여부 |
| `collect_interval_minutes` | `INTEGER` | `NOT NULL` | `60` | 수집 주기(분 단위) |
| `fetch_limit` | `INTEGER` | `NOT NULL` | `20` | 1회 수집 시 최대 항목 수 |
| `is_auto_create_board` | `BOOLEAN` | `NOT NULL` | `FALSE` | 게시판 자동 생성 허용 여부 |
| `is_auto_create_category` | `BOOLEAN` | `NOT NULL` | `TRUE` | 카테고리 자동 생성 허용 여부 |
| `timezone` | `VARCHAR(64)` | `NOT NULL` | `'Asia/Seoul'` | 스케줄 계산 기준 시간대 |
| `last_started_at` | `TIMESTAMPTZ` | `NULL` |  | 마지막 실행 시작 시각 |
| `last_finished_at` | `TIMESTAMPTZ` | `NULL` |  | 마지막 실행 종료 시각 |
| `last_success_at` | `TIMESTAMPTZ` | `NULL` |  | 마지막 성공 시각 |
| `next_run_at` | `TIMESTAMPTZ` | `NULL` |  | 다음 실행 예정 시각 |
| `last_status` | `VARCHAR(24)` | `NOT NULL` | `'IDLE'` | 최신 실행 상태 |
| `last_error_message` | `TEXT` | `NULL` |  | 마지막 오류 메시지 |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | 생성 시각 |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | 수정 시각 |

### 4.3 상태값 규칙

`last_status`는 아래 값을 사용한다.

- `IDLE`
- `RUNNING`
- `SUCCESS`
- `FAILED`

### 4.4 제약 조건

권장 제약은 아래와 같다.

- `PRIMARY KEY (news_job_id)`
- `UNIQUE (job_name)`
- `CHECK (collect_interval_minutes >= 5 AND collect_interval_minutes <= 10080)`
- `CHECK (fetch_limit >= 1 AND fetch_limit <= 100)`

MVP에서는 과도한 스패밍을 막기 위해 `collect_interval_minutes` 최소값을 `5분`으로 둔다.

### 4.5 FK 정의

| FK명 | 참조 컬럼 | 대상 |
| --- | --- | --- |
| `fk_tb_news_collection_jobs_author_user_id__tb_users` | `author_user_id` | `tb_users.user_id` |
| `fk_tb_news_collection_jobs_created_by_user_id__tb_users` | `created_by_user_id` | `tb_users.user_id` |
| `fk_tb_news_collection_jobs_updated_by_user_id__tb_users` | `updated_by_user_id` | `tb_users.user_id` |

### 4.6 인덱스 정의

| 인덱스명 | 컬럼 | 목적 |
| --- | --- | --- |
| `uq_tb_news_collection_jobs_job_name` | `job_name` | 잡 이름 중복 방지 |
| `ix_tb_news_collection_jobs_enabled_next_run_at` | `is_enabled, next_run_at` | due 잡 조회 최적화 |
| `ix_tb_news_collection_jobs_source_type` | `source_type` | 소스 유형별 조회 |
| `ix_tb_news_collection_jobs_author_user_id` | `author_user_id` | 작성 계정별 조회 |
| `ix_tb_news_collection_jobs_created_by_user_id` | `created_by_user_id` | 생성자 기준 조회 |

### 4.7 운영 메모

- `author_user_id`는 유연성을 위해 컬럼으로 두되, MVP 운영 기준값은 `news_bot`으로 고정한다.
- 제어자는 `created_by_user_id`, `updated_by_user_id`로 남기고 실제 게시글 작성자는 `author_user_id`로 분리한다.
- `target_board_slug`와 `target_board_name`은 운영자가 정한다. 외부 API가 게시판명을 마음대로 생성하게 두지 않는다.
- 잡의 on/off, 주기, 대상 게시판, 카테고리 같은 핵심 제어값은 모두 이 테이블을 기준으로 한다.
- 환경변수는 이 테이블 값을 대체하지 않는다.
- 환경변수는 전역 기능 차단이나 공통 timeout 같은 앱 레벨 override가 필요할 때만 선택적으로 사용한다.

### 4.8 `source_config_json` 예시

#### Hacker News

```json
{
  "storyType": "topstories"
}
```

#### DEV_TO

```json
{
  "tag": "backend"
}
```

또는

```json
{
  "username": "ben"
}
```

#### GitHub Releases

```json
{
  "owner": "spring-projects",
  "repo": "spring-boot"
}
```

#### RSS/Atom

```json
{
  "feedUrl": "https://spring.io/blog.atom"
}
```

## 5. `tb_news_collected_items`

### 5.1 용도

이 테이블은 외부 수집 항목의 dedupe와 내부 게시글 연결 상태를 저장한다.

이 테이블이 담당하는 역할은 아래와 같다.

- 같은 외부 항목의 중복 게시 방지
- 외부 항목과 내부 게시글 연결
- 내용 변경 감지
- 최신 동기화 상태 추적

즉, 이 테이블은 `순수 이력 테이블`이 아니라 `실사용 보조 데이터 테이블`이다.

### 5.2 컬럼 정의

| 컬럼명 | 타입 | NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `news_collected_item_id` | `BIGINT` | `NOT NULL` | `GENERATED ALWAYS AS IDENTITY` | 수집 항목 PK |
| `news_job_id` | `BIGINT` | `NOT NULL` |  | 소속 잡 ID |
| `external_item_key` | `VARCHAR(255)` | `NOT NULL` |  | 외부 항목 고유 key |
| `external_url` | `TEXT` | `NOT NULL` |  | 원문 URL |
| `title` | `VARCHAR(255)` | `NOT NULL` |  | 마지막 수집 시점 제목 |
| `payload_hash` | `CHAR(64)` | `NOT NULL` |  | 본문/메타 기준 SHA-256 해시 |
| `published_at` | `TIMESTAMPTZ` | `NULL` |  | 외부 발행 시각 |
| `source_updated_at` | `TIMESTAMPTZ` | `NULL` |  | 외부 소스 수정 시각 |
| `article_id` | `BIGINT` | `NULL` |  | 내부 게시글 ID |
| `last_sync_status` | `VARCHAR(24)` | `NOT NULL` |  | 마지막 동기화 상태 |
| `last_error_message` | `TEXT` | `NULL` |  | 마지막 동기화 오류 메시지 |
| `first_collected_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | 최초 발견 시각 |
| `last_collected_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | 마지막 수집 시각 |
| `last_synced_at` | `TIMESTAMPTZ` | `NULL` |  | 마지막 게시/갱신 반영 시각 |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | 생성 시각 |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | 수정 시각 |

### 5.3 상태값 규칙

`last_sync_status`는 아래 값을 사용한다.

- `CREATED`
- `UPDATED`
- `SKIPPED`
- `FAILED`

### 5.4 제약 조건

권장 제약은 아래와 같다.

- `PRIMARY KEY (news_collected_item_id)`
- `UNIQUE (news_job_id, external_item_key)`

이 유니크 제약이 동일 잡 내 중복 게시 방지의 핵심이다.

### 5.5 FK 정의

| FK명 | 참조 컬럼 | 대상 |
| --- | --- | --- |
| `fk_tb_news_collected_items_news_job_id__tb_news_collection_jobs` | `news_job_id` | `tb_news_collection_jobs.news_job_id` |
| `fk_tb_news_collected_items_article_id__tb_articles` | `article_id` | `tb_articles.article_id` |

### 5.6 인덱스 정의

| 인덱스명 | 컬럼 | 목적 |
| --- | --- | --- |
| `uq_tb_news_collected_items_job_id_external_item_key` | `news_job_id, external_item_key` | 외부 항목 dedupe |
| `ix_tb_news_collected_items_article_id` | `article_id` | 게시글 역참조 |
| `ix_tb_news_collected_items_job_id_last_sync_status` | `news_job_id, last_sync_status` | 관리자 상태 조회 |
| `ix_tb_news_collected_items_job_id_published_at` | `news_job_id, published_at DESC` | 최신 항목 조회 |

### 5.7 운영 메모

- `article_id`는 nullable이다.
- 이유는 아래와 같다.
- 외부 항목은 발견됐지만 게시글 생성 전에 실패할 수 있다.
- 기존 게시글이 소프트 삭제되어도 dedupe 정보는 남겨야 한다.
- `payload_hash`는 `제목 + URL + 요약 본문 + 발행 시각` 등 게시글 생성 결과에 영향을 주는 필드를 기준으로 계산한다.

### 5.8 `external_item_key` 예시

- Hacker News: `hn:item:8863`
- DEV API: `dev:article:123456`
- GitHub Releases: `github:spring-projects/spring-boot:tag:v3.5.0`
- RSS/Atom: `rss:https://spring.io/blog.atom:guid:abcd-1234`

## 6. 관계 요약

### 6.1 관계 구조

```text
tb_users(admin) ---< tb_news_collection_jobs >--- tb_users(news_bot)
                           |
                           v
               tb_news_collected_items --- tb_articles
```

정확히 풀면 아래와 같다.

- `tb_news_collection_jobs.created_by_user_id`
  - 잡을 만든 관리자 계정 참조
- `tb_news_collection_jobs.updated_by_user_id`
  - 마지막 수정 관리자 계정 참조
- `tb_news_collection_jobs.author_user_id`
  - 실제 게시글 작성자 계정 참조
- `tb_news_collected_items.news_job_id`
  - 어느 잡이 이 항목을 수집했는지 참조
- `tb_news_collected_items.article_id`
  - 이 외부 항목이 어떤 내부 게시글로 연결됐는지 참조

### 6.2 왜 `tb_boards` FK를 직접 두지 않나

MVP에서는 `target_board_slug`를 기준으로 게시판을 찾거나 자동 생성하는 방식을 택한다.

이유는 아래와 같다.

- 게시판 자동 생성이 요구사항에 포함되어 있다.
- 잡 저장 시점에는 아직 게시판이 없을 수 있다.
- 운영자가 slug와 표시명을 명시적으로 제어할 수 있어야 한다.

대신 운영 기준은 엄격하게 둔다.

- `1 job = 1 target board`
- `is_auto_create_board` 기본값은 `FALSE`
- 외부 API에서 넘어온 임의 값으로 새 게시판을 만들지 않는다
- 자동 생성은 운영자가 등록한 slug/name 쌍에 한해서만 허용한다

### 6.3 왜 `tb_article_categories` FK를 직접 두지 않나

카테고리도 게시판 생성 여부와 연결되어 있어 잡 저장 시점에 항상 존재한다고 볼 수 없다.

따라서 MVP에서는 아래 정책을 택한다.

- `target_category_name`을 저장한다
- 실행 시 게시판 내 동일 이름 카테고리를 찾는다
- 없고 `is_auto_create_category = TRUE`면 생성한다

## 7. 이력용인지, 실사용 보조 데이터인지

정리하면 아래와 같다.

### `tb_news_collection_jobs`

- 주목적: 운영 제어
- 부목적: 최신 실행 상태 요약
- 성격: 이력 전용 아님

### `tb_news_collected_items`

- 주목적: dedupe 및 게시글 동기화 보조
- 부목적: 최신 상태 추적
- 성격: 이력 전용 아님

즉, 두 테이블 모두 `유저에게 직접 보여주는 게시글 본문 데이터`를 담는 메인 테이블은 아니지만, 실제 게시글 운영을 위해 반드시 필요한 보조 데이터다.

## 8. 후속 확장 메모

향후 아래 요구가 생기면 추가 테이블을 검토한다.

- 실행 단위 상세 이력 조회
- 항목별 재처리 큐
- 다중 시스템 작성자(`news_bot_tech`, `news_bot_devops`) 분리
- 관리자 화면에서 실행 로그 페이지 제공

후속 후보:

- `tb_news_job_executions`
- `tb_news_job_execution_items`
