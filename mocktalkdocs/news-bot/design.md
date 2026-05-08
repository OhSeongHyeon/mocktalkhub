# News Bot Design

## 1. 설계 목표

- 기존 `board / article / article_category` 모델을 최대한 재사용한다.
- 외부 API 호출, 잡 스케줄링, 게시글 생성 로직을 분리한다.
- 새소식 기능이 실패해도 기존 커뮤니티 기능에 영향을 최소화한다.
- 최소 백오피스 화면과 관리자 API를 함께 운영 가능하게 한다.

외부 소스별 입력값과 품질 차이에 대한 운영 설명은 `external-sources-guide.md`를 참고한다.

## 2. 제안 아키텍처

### 2.1 구성 요소

- `AdminNewsBotController`
- `AdminNewsBotService`
- `NewsBotScheduler`
- `NewsBotDispatchService`
- `NewsBotJobExecutor`
- `NewsBotJobExecutionClaimService`
- `NewsBotJobExecutionPersistenceService`
- `NewsSourceClient` 인터페이스와 소스별 구현체
- `NewsBotSourceFetchService`
- `NewsBotBoardProvisionService`
- `NewsArticlePublishService`

### 2.2 패키지 제안

```text
com.mocktalkback.domain.newsbot/
├─ controller/
├─ dto/
├─ entity/
├─ repository/
├─ service/
├─ type/
└─ config/

com.mocktalkback.infra.newsbot/
├─ HackerNewsSourceClient
├─ DevToSourceClient
├─ GitHubReleasesSourceClient
└─ RssSourceClient
```

## 3. 데이터 모델 제안

## 3.1 `tb_news_collection_jobs`

잡 정의와 마지막 실행 상태를 저장한다.

권장 컬럼:

- `news_job_id`
- `job_name`
- `source_type`
- `source_config_json`
- `target_board_slug`
- `target_board_name`
- `target_category_name`
- `author_user_id`
- `created_by_user_id`
- `updated_by_user_id`
- `is_enabled`
- `collect_interval_minutes`
- `fetch_limit`
- `is_auto_create_board`
- `is_auto_create_category`
- `timezone`
- `last_started_at`
- `last_finished_at`
- `last_success_at`
- `next_run_at`
- `last_status`
- `last_error_message`
- `created_at`
- `updated_at`

설계 이유:

- 스케줄 변경을 DB에서 즉시 반영하려면 잡 정의가 필요하다.
- `target_board_slug`를 저장하면 게시판이 삭제/복구되더라도 slug 기준 재생성이 쉽다.
- `author_user_id`를 잡별로 고정하면 현재는 `news_bot`을 기본으로 쓰되, 향후 시스템 작성 계정 분리가 필요할 때 유연하다.

## 3.2 `tb_news_collected_items`

외부 항목 dedupe와 내부 게시글 연결 상태를 저장한다.

권장 컬럼:

- `news_collected_item_id`
- `news_job_id`
- `source_type`
- `external_item_key`
- `external_url`
- `title`
- `payload_hash`
- `published_at`
- `source_updated_at`
- `article_id`
- `sync_status`
- `last_synced_at`
- `created_at`
- `updated_at`

권장 제약:

- `UNIQUE(news_job_id, external_item_key)`

설계 이유:

- 외부 항목 단위 중복 방지가 핵심이다.
- 원문 URL만으로 중복 판별하면 정확하지 않다.
- 나중에 동일 항목 `update` 정책을 넣을 때 `payload_hash`가 필요하다.

## 3.3 왜 2개가 최소인가

- `jobs`만 있으면 스케줄 제어는 가능하지만 중복 방지가 취약하다.
- `collected_items`만 있으면 운영자가 주기/on/off를 조정할 수 없다.
- 실행 이력 전용 3번째 테이블은 일단 만들지 않고, 요약 상태는 `jobs`에 저장하고 관리자 액션은 `tb_admin_audit_logs`를 활용한다.

## 4. 스케줄링 방식

정적 cron 기반 `@Scheduled(cron = "${...}")`는 이 요구사항과 맞지 않는다.

이유:

- 운영자가 DB에서 잡 간격을 바꿔도 애플리케이션 프로퍼티는 즉시 바뀌지 않는다.
- 잡 개수가 늘어나면 소스별로 `@Scheduled` 메서드를 추가하는 구조가 된다.

권장 방식은 `dispatcher poller`다.

### 4.1 동작 방식

- 애플리케이션에는 고정 주기 poller 하나만 둔다.
- 예: `@Scheduled(fixedDelayString = "${app.news-bot.dispatcher-interval-ms:60000}")`
- 이 poller는 `enabled = true` 이고 `next_run_at <= now()` 인 잡만 조회한다.
- 잡 실행이 끝나면 `next_run_at = now + interval_minutes` 로 갱신한다.
- 수동 `run now`와 자동 스케줄 실행이 겹쳐도 동일 잡은 한 번만 선점 실행한다.
- 이미 실행 중인 잡은 중복 실행하지 않는다.
- 운영자 수정/비활성화는 허용하지만, 이미 시작된 실행 1회는 즉시 중단하지 않고 다음 실행부터 변경을 반영한다.

### 4.2 장점

- 백오피스 변경이 곧바로 다음 poll cycle에 반영된다.
- on/off와 주기 변경이 단순하다.
- 나중에 잡 개수가 늘어나도 스케줄러 구조가 거의 바뀌지 않는다.

### 4.3 환경변수 정책

- 잡별 on/off, 주기, 대상 게시판 같은 운영 설정은 DB를 기준으로 한다.
- `.env.dev`, `.env.prod`에 뉴스봇 전용 값을 반드시 추가해야 하는 구조는 피한다.
- 환경변수는 아래처럼 앱 전역 override 용도로만 선택적으로 지원한다.
- 전역 enable/disable
- dispatcher polling interval
- 외부 HTTP connect/read timeout
- 공통 `User-Agent`
- 기본 timezone

즉, 환경변수는 `필수 설정`이 아니라 `운영 안전장치`다.

### 4.4 동시성 처리

- 현재 구현은 상태 선점 update 방식으로 동일 잡 중복 실행을 막는다.
- 선점은 `REQUIRES_NEW` 트랜잭션에서 먼저 커밋하고, 외부 API 호출은 그 이후에 수행한다.
- 비정상 종료로 `RUNNING` 상태가 고착되는 것을 대비해 stale timeout 기준 재선점 허용 시간을 둔다.

## 5. 외부 소스 어댑터 설계

공통 인터페이스 예시:

```java
public interface NewsSourceClient {
    NewsSourceType supports();
    List<NewsBotSourceItem> fetchItems(Map<String, Object> sourceConfig, int limit);
}
```

## 5.1 Hacker News

- 입력: `storyType(topstories/newstories/beststories)`, `limit`
- 수집 흐름:
- story id 목록 조회
- 상위 N개 item 상세 조회
- 링크형 게시글 생성

주의:

- 댓글성 item, dead/deleted item 제외
- 외부 링크가 없는 경우 HN item URL로 대체

## 5.2 DEV API

- 입력: `tag` 또는 `username`, `perPage`
- 수집 흐름:
- 공개 article 목록 조회
- 제목, 설명, URL, 발행시각 추출

주의:

- 공식 인증 없는 공개 endpoint 사용 전제
- `User-Agent` 기본 헤더 유지

## 5.3 GitHub Releases

- 입력: `owner`, `repo`
- 수집 흐름:
- `/repos/{owner}/{repo}/releases/latest` 조회
- release id/tag/body/html_url 추출

주의:

- 공개 저장소만 대상
- 무인증 rate limit이 낮다
- 다수 repo를 고빈도로 조회하면 금방 한도에 걸릴 수 있다

## 5.4 RSS/Atom

- 입력: `feedUrl`
- 수집 흐름:
- feed XML 조회
- item 또는 entry 파싱
- guid/link/title/published 추출

주의:

- RSS/Atom 형식 차이가 있으므로 공통 파서가 필요하다
- MVP는 JDK XML 파서로 시작하고, 필요 시 별도 feed 라이브러리 도입을 검토한다

## 6. 게시판/카테고리/게시글 생성 전략

## 6.1 전용 봇 사용자

`tb_articles.user_id`가 필수이므로 전용 내부 계정이 필요하다.

권장 역할 분리:

- 제어자: `admin`
- 작성자: `news_bot`

권장 작성 계정:

- loginId: `news_bot`
- handle: `news_bot`
- role: `WRITER`

권장 이유:

- `admin`이 직접 작성자로 들어가면 운영 액션과 자동 생성 콘텐츠의 주체가 섞인다.
- `news_bot`을 시스템 작성자로 고정하면 나중에 데이터가 많아져도 출처와 책임 구분이 유지된다.
- 시스템 계정은 일반 회원가입 흐름과 분리하는 편이 안전하다.

운영 원칙:

- `news_bot`은 일반 회원가입으로 만들지 않는다.
- Flyway seed 또는 앱 초기화 단계에서 존재를 보장한다.
- 백오피스에서 잡을 만드는 사용자는 `admin`이지만, 생성된 게시글의 `user_id`는 `news_bot`으로 적재한다.

## 6.2 게시판 자동 생성

게시판이 없으면 아래 기본값으로 생성한다.

- `visibility = PUBLIC`
- `article_write_policy = OWNER`
- `description = 외부 새소식 자동 수집 게시판`

추가 처리:

- 봇 사용자를 `tb_board_members`의 `OWNER`로 등록한다.

이유:

- 사람이 실수로 해당 게시판에 일반 글을 쓰지 않게 할 수 있다.
- 봇이 OWNER면 이후에도 안정적으로 글을 쓸 수 있다.

## 6.3 카테고리 자동 생성

- 기존 `ArticleImportService.ensureCategory(...)` 패턴과 동일하게 board + categoryName 기준으로 조회 후 없으면 생성한다.
- 비교는 대소문자 무시 기준을 따른다.

## 6.4 게시글 매핑 규칙

- `title`: 외부 항목 제목
- `content_source`: Markdown 템플릿 본문
- `content`: 기존 렌더링 서비스로 생성된 HTML
- `content_format`: `MARKDOWN`
- `visibility`: `PUBLIC`
- `notice`: `false`

본문 예시:

```markdown
원문: https://...

출처: GitHub Releases
발행시각: 2026-03-15T08:00:00Z

## 요약
릴리즈 노트 또는 설명 본문
```

## 6.5 동일 항목 업데이트 정책

- 동일 `external_item_key`가 없으면 새 글 생성
- 동일 key + 동일 `payload_hash`면 skip
- 동일 key + hash 변경이면 기존 article 업데이트

## 7. 관리자 API 제안

### 7.1 필수 API

- `GET /api/admin/news-bot/jobs`
- `POST /api/admin/news-bot/jobs`
- `PUT /api/admin/news-bot/jobs/{jobId}`
- `PATCH /api/admin/news-bot/jobs/{jobId}/enabled`
- `POST /api/admin/news-bot/jobs/{jobId}/run`

### 7.2 최소 백오피스 화면

- 현재는 `/admin/news-bot` 경로의 최소 백오피스 화면이 구현되어 있다.
- 목록, 생성/수정, on/off, 즉시 실행, 최근 실행 결과 확인이 가능하다.
- `MANAGER`, `ADMIN` 권한 사용자가 접근 가능한 구조를 기준으로 한다.

## 7.3 백오피스 폼 UX 세분화 권장안

현재 뉴스봇 생성/수정 폼은 단일 긴 폼으로 동작하지만, 운영자 실수를 줄이려면 아래 다섯 구역으로 나누는 편이 좋다.

### 7.3.1 공통 정보

- `jobName`
- `sourceType`

설계 의도:

- 운영자가 먼저 "이 잡이 무엇을 위한 잡인지"를 명확히 인식하게 한다.
- `sourceType`이 바뀌면 아래 소스별 필드 구성도 함께 바뀌어야 한다.

### 7.3.2 외부 소스 조건

- `HACKER_NEWS`
  - `storyType`
- `DEV_TO`
  - UI 전용 `mode = tag | username`
  - mode가 `tag`면 `devTag`만 노출
  - mode가 `username`이면 `devUsername`만 노출
- `GITHUB_RELEASES`
  - `githubOwner`
  - `githubRepo`
- `RSS`
  - `rssFeedUrl`

설계 의도:

- 외부 검색 조건과 내부 적재 정보를 시각적으로 분리한다.
- 특히 DEV는 `tag`와 `username`을 동시에 보여주지 않는 편이 낫다.
- 현재 API payload는 `sourceConfig`를 그대로 유지하되, UI만 모드 기반으로 세분화한다.

### 7.3.3 내부 적재 정보

- `targetBoardSlug`
- `targetBoardName`
- `targetCategoryName`

설계 의도:

- "무엇을 가져올지"와 "어디에 넣을지"를 운영자가 혼동하지 않게 한다.
- `targetBoardName`은 `autoCreateBoard = true`일 때만 노출하거나 강조하는 편이 좋다.

### 7.3.4 실행 정책

- `collectIntervalMinutes`
- `fetchLimit`
- `timezone`

설계 의도:

- 수집 빈도와 양을 한 구역에서 같이 조절하게 한다.
- `timezone`은 기본값 `Asia/Seoul`이면 고급 설정 구역으로 내려도 된다.
- `collectIntervalMinutes`는 자유 입력 외에 추천 preset을 함께 제공하는 편이 좋다.
- `fetchLimit`도 `5`, `10`, `20` 같은 추천값을 제공하면 좋다.

### 7.3.5 자동 생성 정책

- `autoCreateBoard`
- `autoCreateCategory`

설계 의도:

- 자동 생성은 운영 리스크가 있으므로 별도 구역으로 분리해 경고 문구와 함께 보여준다.
- `autoCreateBoard = false`가 기본값인 이유를 화면에서 설명해야 한다.

### 7.3.6 조건부 노출 규칙

권장 UX 규칙:

- `sourceType` 변경 시 다른 소스 전용 필드는 초기화
- `DEV_TO`는 `tag` 또는 `username` 중 하나만 입력 가능
- `autoCreateBoard = false`면 `targetBoardName`은 숨기거나 보조 텍스트 수준으로만 표시
- `timezone = Asia/Seoul` 기본값이면 접힌 고급 설정으로 이동 가능

### 7.3.7 운영 기본값 제안

- `collectIntervalMinutes`
  - Hacker News: `180`
  - DEV: `180`
  - GitHub Releases: `720`
  - RSS: `360`
- `fetchLimit`
  - Hacker News: `10`
  - DEV: `10`
  - GitHub Releases: `1`
  - RSS: `8`
- `autoCreateBoard = false`
- `autoCreateCategory = true`

### 7.3.8 필수 입력 하이라이트

- 필수 입력값이 비어 있으면 상단 에러만 띄우지 않고 해당 필드를 함께 하이라이트한다.
- 공통 필드와 소스별 조건부 필수 필드 모두 동일 기준으로 표시한다.
- `autoCreateBoard = true`일 때 `targetBoardName`도 필수 하이라이트 대상에 포함한다.

## 8. 오류 처리 및 복구

- 외부 API 타임아웃은 잡 단위 실패로 처리한다.
- 실패해도 전체 스케줄러 루프는 계속 돌아야 한다.
- 마지막 오류 메시지는 `tb_news_collection_jobs.last_error_message`에 저장한다.
- 수동 `run now`와 설정 변경은 `tb_admin_audit_logs`에 남긴다.
- 운영 제어는 기계 동작보다 우선하지만, 이미 시작된 실행을 중간 취소하는 모델은 기본 범위에 포함하지 않는다.
- 따라서 `running` 중 수정/비활성화는 허용하되, 효과는 다음 실행부터 반영하는 것을 기본 정책으로 둔다.

## 9. 재사용 가능한 기존 코드

- 외부 HTTP 호출: `RestClient`
- 환경 프로퍼티 패턴: `ContentMarketProperties`
- 스케줄러 활성화: `SchedulingConfig`
- 관리자 API 구조: `AdminContentMarketController`, `AdminBoardController`
- 카테고리 자동 생성 패턴: `ArticleImportService.ensureCategory(...)`

## 10. 구현 시 주의점

- `ArticleService.create()`는 현재 인증 사용자와 request.userId 일치를 강제하므로 배치에서 그대로 재사용하기 어렵다.
- 따라서 내부 배치 전용 게시글 발행 서비스가 별도로 필요하다.
- 외부 API 호출과 DB 저장을 하나의 긴 트랜잭션으로 묶지 않는다.
- GitHub 무인증 호출은 `60/hour` 제한이 있으므로 저장소 수가 늘면 캐시 또는 수집 주기 상향이 필요하다.
