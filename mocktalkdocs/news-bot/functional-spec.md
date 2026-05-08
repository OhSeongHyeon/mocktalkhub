# News Bot Functional Spec

## 1. 기능 개요

`news-bot`은 운영자가 등록한 수집 잡 정의를 기준으로 외부 새소식을 가져와 내부 게시판에 자동 게시하는 기능이다.

핵심 사용자 시나리오는 `운영자가 새소식 수집 규칙을 만들고, 백엔드가 주기적으로 실행하며, 새 게시판/카테고리/게시글을 자동 생성하는 것`이다.

## 2. 사용자 시나리오

### UC-01. 운영자가 새 수집 잡을 만든다

- 운영자는 공통 정보 구역에서 잡 이름과 소스 유형을 선택한다.
- 운영자는 외부 소스 조건 구역에서 sourceType에 맞는 필드만 입력한다.
- 운영자는 내부 적재 정보 구역에서 대상 게시판/카테고리를 지정한다.
- 운영자는 실행 정책 구역에서 주기, 최대 수집 건수, timezone을 조정한다.
- 운영자는 자동 생성 정책 구역에서 게시판/카테고리 자동 생성 여부를 선택한다.
- 시스템은 저장 직후 다음 실행 시각을 계산한다.

### UC-02. 운영자가 잡을 비활성화한다

- 운영자는 특정 잡을 off로 변경한다.
- 시스템은 이후 스케줄 루프에서 해당 잡을 실행하지 않는다.
- 이미 시작된 실행 1회는 즉시 중단하지 않는다.
- 비활성화 변경은 다음 실행부터 반영된다.

### UC-03. 스케줄러가 새소식을 자동 수집한다

- dispatcher가 due 잡을 찾는다.
- 소스 어댑터가 외부 항목 목록을 가져온다.
- 시스템이 dedupe를 수행한다.
- 게시판/카테고리가 없으면 자동 생성한다.
- 새 게시글을 작성한다.
- 실행 결과와 마지막 상태를 기록한다.

### UC-04. 운영자가 즉시 실행한다

- 운영자는 특정 잡에 대해 `run now`를 호출한다.
- 시스템은 잡 1회를 바로 실행한다.
- 마지막 실행 결과를 응답으로 돌려준다.
- 동일 잡이 이미 실행 중이면 중복 실행은 막고 충돌 응답을 반환한다.

## 3. 잡 상태 모델

권장 상태값:

- `IDLE`
- `RUNNING`
- `SUCCESS`
- `FAILED`

의미:

- `IDLE`: 대기 중
- `RUNNING`: 현재 실행 중
- `SUCCESS`: 전체 성공
- `FAILED`: 전체 실패

## 4. 수집 항목 상태 모델

권장 상태값:

- `CREATED`
- `UPDATED`
- `SKIPPED`
- `FAILED`

정책:

- 기존 key 없음: `CREATED`
- 기존 key 있고 hash 동일: `SKIPPED`
- 기존 key 있고 hash 다름: `UPDATED`
- 본문 생성/저장 중 오류: `FAILED`

## 5. 백오피스 폼 구조

운영자용 폼은 아래 구역으로 나누는 것을 기준으로 한다.

- 공통 정보
- 외부 소스 조건
- 내부 적재 정보
- 실행 정책
- 자동 생성 정책

### 5.1 공통 정보

- `jobName`
- `sourceType`

### 5.2 외부 소스 조건

- `HACKER_NEWS`
  - `storyType`
- `DEV_TO`
  - UI 전용 `mode = tag | username`
  - `mode = tag`면 `devTag`
  - `mode = username`이면 `devUsername`
- `GITHUB_RELEASES`
  - `githubOwner`
  - `githubRepo`
- `RSS`
  - `rssFeedUrl`

### 5.3 내부 적재 정보

- `targetBoardSlug`
- `targetBoardName`
- `targetCategoryName`

### 5.4 실행 정책

- `collectIntervalMinutes`
- `fetchLimit`
- `timezone`

### 5.5 자동 생성 정책

- `autoCreateBoard`
- `autoCreateCategory`

## 6. 잡별 입력 규격

## 6.1 Hacker News

필수 입력:

- `sourceType = HACKER_NEWS`
- `storyType = topstories | newstories | beststories`
- `targetBoardSlug`

선택 입력:

- `targetBoardName`
- `targetCategoryName`
- `collectIntervalMinutes`
- `fetchLimit`
- `timezone`

## 6.2 DEV API

필수 입력:

- `sourceType = DEV_TO`
- `mode = tag | username`
- `mode = tag`면 `devTag`
- `mode = username`이면 `devUsername`
- `targetBoardSlug`

선택 입력:

- `targetBoardName`
- `targetCategoryName`
- `collectIntervalMinutes`
- `fetchLimit`
- `timezone`

## 6.3 GitHub Releases

필수 입력:

- `sourceType = GITHUB_RELEASES`
- `owner`
- `repo`
- `targetBoardSlug`

선택 입력:

- `targetBoardName`
- `targetCategoryName`
- `collectIntervalMinutes`
- `fetchLimit`
- `timezone`

## 6.4 RSS/Atom

필수 입력:

- `sourceType = RSS`
- `feedUrl`
- `targetBoardSlug`

선택 입력:

- `targetBoardName`
- `targetCategoryName`
- `collectIntervalMinutes`
- `fetchLimit`
- `timezone`

## 7. 폼 동작 규칙

- `sourceType` 변경 시 이전 소스 전용 입력값은 초기화한다.
- `DEV_TO`는 `tag`와 `username`을 동시에 노출하지 않는다.
- `autoCreateBoard = false`일 때 `targetBoardName`은 숨기거나 비강조 처리한다.
- `timezone`은 기본값 `Asia/Seoul`을 제공하고, 고급 설정으로 내려도 된다.
- `collectIntervalMinutes`, `fetchLimit`는 자유 입력과 추천 preset을 함께 제공하는 편이 좋다.
- 필수 입력값이 비어 있으면 해당 필드 자체를 하이라이트한다.

## 8. 게시판 자동 생성 규칙

- slug 기준으로 게시판을 조회한다.
- 없으면 새 게시판을 만든다.
- 기본 가시성은 `PUBLIC`
- 기본 작성 정책은 `OWNER`
- 생성 직후 봇 사용자를 OWNER 멤버로 넣는다.

## 9. 카테고리 자동 생성 규칙

- 게시판 내 `categoryName` 기준으로 조회한다.
- 없고 `autoCreateCategory = true` 면 생성한다.
- 없고 `autoCreateCategory = false` 면 해당 항목은 실패 처리한다.

## 10. 게시글 생성 규칙

필수 값 매핑:

- `board_id`: 대상 게시판
- `user_id`: 시스템 작성자 `news_bot`의 `author_user_id`
- `article_category_id`: 설정 카테고리 또는 자동 생성 카테고리
- `title`: 외부 제목
- `content_source`: Markdown 템플릿
- `content_format`: `MARKDOWN`
- `visibility`: `PUBLIC`
- `is_notice`: `false`

본문 필수 포함 요소:

- 원문 링크
- 출처 이름
- 외부 발행 시각
- 원문 요약 또는 본문 일부

## 11. 관리자 API 계약 초안

### 11.1 잡 목록 조회

- `GET /api/admin/news-bot/jobs`
- 응답:
- job id
- 이름
- 소스 유형
- 활성화 여부
- 주기
- 다음 실행 시각
- 마지막 성공 시각
- 마지막 상태

### 11.2 잡 생성

- `POST /api/admin/news-bot/jobs`
- 요청:
- 이름
- 소스 유형
- 소스 설정
- 게시판/카테고리 매핑
- 주기
- fetch limit
- 게시판 자동 생성 여부
- 카테고리 자동 생성 여부
- timezone

### 11.3 잡 수정

- `PUT /api/admin/news-bot/jobs/{jobId}`
- 수정 가능:
- 이름
- 소스 유형
- 소스 설정
- 주기
- 대상 게시판/카테고리
- fetch limit
- 게시판 자동 생성 여부
- 카테고리 자동 생성 여부
- timezone
- 실행 중 수정도 허용한다.
- 다만 이미 시작된 실행은 즉시 중단되거나 중간 설정이 바뀌지 않는다.
- 수정된 값은 다음 실행부터 반영되는 것을 기준으로 한다.

### 11.4 잡 토글

- `PATCH /api/admin/news-bot/jobs/{jobId}/enabled`

### 11.5 즉시 실행

- `POST /api/admin/news-bot/jobs/{jobId}/run`
- 응답:
- 실행 시각
- 총 수집 개수
- 생성 개수
- 갱신 개수
- 스킵 개수
- 실패 개수
- 동일 잡이 이미 `RUNNING` 상태이면 중복 실행을 허용하지 않고 충돌 응답으로 처리한다.

## 12. 권한

현재 구현 기준 권한:

- `MANAGER`, `ADMIN`: 뉴스봇 잡 목록/생성/수정/비활성화/즉시 실행 가능

계정 역할 분리:

- `admin`: 백오피스 제어자
- `news_bot`: 시스템 게시글 작성자

## 13. 장애 시나리오

### FEED 조회 실패

- 잡 상태 `FAILED`
- 마지막 오류 메시지 저장
- 다음 주기에는 다시 실행

### 대상 게시판 자동 생성 실패

- 해당 항목 또는 전체 잡 실패
- 원인 메시지 저장

### 게시글 저장 중 유니크 충돌

- 현재 구현은 `(news_job_id, external_item_key)` 유니크 제약과 실행 선점 로직으로
  동일 잡의 중복 저장 가능성을 먼저 낮춘다.
- 별도의 충돌 재판단 로직은 두지 않는다.
- 운영 중 예외적인 DB 유니크 충돌이 발생하면 장애로 간주하고 원인 확인 후 재실행한다.

### 일부 항목만 실패

- 현재 구현 기준으로는 전체 잡 상태를 `FAILED`로 기록한다.
- 성공한 항목 반영 결과는 유지하고, 첫 오류 메시지를 마지막 오류로 저장한다.

## 14. MVP와 후속 범위

### MVP

- 잡 목록/생성/수정
- on/off
- interval 단위 주기 제어
- run now
- HN / DEV / GitHub Releases / RSS 지원
- 게시판/카테고리 자동 생성
- dedupe + update
- 관리자 화면

### 후속

- 소스별 세부 필터
- 번역/요약
- 이미지 썸네일 추출
- 다국어 게시판 자동 분기
