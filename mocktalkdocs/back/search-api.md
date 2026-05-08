# 검색 API

## 개요

- 종합검색은 `/search` 페이지에서 사용한다.
- 백엔드는 `Native SQL(FTS/ILIKE 후보 ID 조회) + QueryDSL/JPA(엔티티 적재)` 조합으로 검색을 수행한다.
- FTS는 PostgreSQL `tsvector + plainto_tsquery('simple', ...)` 기반이고, 부족한 결과는 `ILIKE + pg_trgm similarity` 로 보완한다.

## 엔드포인트

### `GET /api/search`

- 설명: 게시판/게시글/댓글/사용자 통합 검색
- 인증: 비로그인 허용, 단 가시성 규칙 적용

### 요청 파라미터

- `q` 필수
- `type` 선택
  - `ALL|BOARD|ARTICLE|COMMENT|USER`
  - 기본값: `ALL`
- `order` 선택
  - `LATEST|OLDEST`
  - 기본값: `LATEST`
- `page` 선택
  - 0부터 시작
- `size` 선택
  - 기본 10, 최대 50
- `boardSlug` 선택
  - 게시글/댓글 검색에만 적용되는 필터

## 검색 대상 필드

- 게시판
  - `board_name`, `slug`, `description`
- 게시글
  - FTS: `title`, `content`
  - fallback 1차: `title`, `author_search_text`
  - fallback 2차: `content`
- 댓글
  - `content`
- 사용자
  - `handle`, `display_name`, `user_name`

## 검색 동작

### 1. 공통 흐름

1. Native SQL로 우선 후보 ID를 찾는다.
2. 부족하면 fallback SQL로 보충한다.
3. 최종 ID 순서를 유지한 채 QueryDSL/JPA로 엔티티를 적재한다.
4. 응답 DTO로 조합해 `SliceResponse` 로 반환한다.

즉, “검색 순위 계산”과 “응답 조립”을 분리한 구조다.

### 2. 섹션별 fallback

#### 게시판

- 1차: FTS
- 2차: `ILIKE + similarity`

#### 게시글

- 1차: FTS
- 2차: 제목/작성자 우선 fallback
  - `title`
  - `author_search_text`
- 3차: 본문 fallback
  - `content`

현재 게시글은 단일 `ILIKE OR` 보강이 아니라, `제목/작성자 -> 본문` 2단계 fallback 구조다.

#### 댓글

- 1차: FTS
- 2차: `content ILIKE` fallback

#### 사용자

- 1차: FTS
- 2차: `handle/display_name/user_name ILIKE` fallback

## 검색어 규칙

- `q` 는 trim 후 비어 있으면 에러 처리된다.
- 최소 길이 제한은 없다.
- FTS는 `plainto_tsquery('simple', :keyword)` 기준으로 수행한다.

## 정렬 규칙

### FTS 결과

- 1순위: `ts_rank DESC`
- 2순위: `order` 에 따른 created/updated/id 보조 정렬

### fallback 결과

- 1순위: `pg_trgm similarity` 기반 유사도 내림차순
- 2순위: `order` 에 따른 created/updated/id 보조 정렬

즉, `LATEST/OLDEST` 는 완전한 1순위 정렬이 아니라 검색 relevance 의 동점 보조 기준이다.

## 가시성 / 접근 규칙

검색도 게시판/게시글 가시성 정책을 그대로 따른다.

- 비로그인
  - `PUBLIC` 게시판
  - `PUBLIC` 게시글/댓글
- 로그인 일반 사용자
  - `PUBLIC` 게시판
    - 게시글 visibility `PUBLIC`, `MEMBERS`
    - `OWNER/MODERATOR` 는 `MODERATORS` 도 조회 가능
  - `GROUP` 게시판
    - `PUBLIC`
    - 활성 멤버는 `MEMBERS`
    - `OWNER/MODERATOR` 는 `MODERATORS`
  - `PRIVATE` 게시판
    - `OWNER` 만 `PUBLIC/MEMBERS/MODERATORS`
  - `UNLISTED`
    - 조회 불가
- 관리자(`MANAGER/ADMIN`)
  - 전체 허용

추가 규칙:

- `BANNED` 멤버는 검색 노출 대상에서 제외된다.
- `boardSlug` 필터는 게시글/댓글 검색 SQL에만 적용된다.

## 응답 형식

```json
{
  "success": true,
  "data": {
    "boards": { "items": [], "page": 0, "size": 10, "hasNext": false, "hasPrevious": false },
    "articles": { "items": [], "page": 0, "size": 10, "hasNext": false, "hasPrevious": false },
    "comments": { "items": [], "page": 0, "size": 10, "hasNext": false, "hasPrevious": false },
    "users": { "items": [], "page": 0, "size": 10, "hasNext": false, "hasPrevious": false }
  }
}
```

각 섹션은 `SliceResponse` 이므로 전체 건수/전체 페이지 수는 제공하지 않는다.

## 응답 메모

- `type=ALL` 이 아닌 경우에도 다른 섹션은 빈 `SliceResponse` 로 반환된다.
- `type=ALL` 이어도 각 섹션은 동일한 `page/size` 값을 공유한다.
- 게시판 섹션은 대표 이미지가 있으면 함께 내려준다.
- 게시글 섹션은 댓글 수, 좋아요/싫어요 수, `notice` 여부를 함께 내려준다.

## 현재 구현 기준 요약

- 검색 후보 선별은 Native SQL
- 응답 조립은 QueryDSL/JPA
- fallback 은 단순 `OR` 한 번이 아니라 섹션별로 나뉘어 있다
- 응답은 전부 Slice 기반

## 테스트 포인트

- `type` 별 응답 분기
- `boardSlug` 필터 전달
- 기본 페이지/최대 페이지 크기
- FTS SQL 로딩
- Native SQL 파라미터 바인딩

## 참고 파일

- `mocktalkback/src/main/java/com/mocktalkback/domain/search/controller/SearchController.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/search/service/SearchService.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/search/service/SearchNativeQueryExecutor.java`
- `mocktalkback/src/main/resources/sql/search/board_ids_fts.sql`
- `mocktalkback/src/main/resources/sql/search/article_ids_fts.sql`
- `mocktalkback/src/main/resources/sql/search/article_ids_ilike_primary.sql`
- `mocktalkback/src/main/resources/sql/search/article_ids_ilike_content.sql`
- `mocktalkback/src/main/resources/sql/search/comment_ids_fts.sql`
- `mocktalkback/src/main/resources/sql/search/user_ids_fts.sql`
