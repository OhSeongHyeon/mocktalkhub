# Redis 활용 현황 및 후보 정리

이 문서는 현재 백엔드에서 Redis를 실제로 어디에 쓰고 있는지와, 아직 후보로 남아 있는 항목을 구분해 정리한 참고 자료입니다.

## 1. 현재 사용 중인 영역

### 1.1 Refresh Token 회전

- 목적: Refresh 세션의 `sid/jti` 회전과 absolute TTL 관리
- 키
  - `rt:sid:<sid>`
  - `rt:sid:abs:<sid>`
- 특징
  - Lua 스크립트로 원자적 회전
  - 인증 핵심 경계

### 1.2 OAuth2 1회용 코드

- 목적: OAuth2 성공 후 프론트 콜백에서 Access Token으로 교환할 1회용 코드 저장
- 키
  - `oauth:code:<code>`
- 특징
  - 짧은 TTL
  - 소비 시 `get + delete`

### 1.3 알림 presence

- 목적: 사용자가 어떤 화면을 보고 있는지, 알림 패널이 열려 있는지 heartbeat 상태 저장
- 저장소
  - `NotificationPresenceRedisStore`
- 특징
  - Redis 우선
  - 실패 시 `NotificationPresenceService` 가 메모리 fallback 사용
  - unread push 억제와 “현재 글 보고 있음” 판정에 사용

### 1.4 실시간 연결 ticket

- 목적: `EventSource` 연결용 1회용 ticket 저장
- 저장소
  - `NotificationRealtimeTicketStore`
- 특징
  - `REALTIME_CONNECT` 채널
  - 짧은 TTL
  - consume 시 삭제

### 1.5 실시간 이벤트 pub/sub

- 목적: 알림/게시판 SSE 이벤트를 다중 인스턴스에서도 전파 가능한 구조로 유지
- 저장소
  - `RealtimeRedisPublisher`
- 특징
  - Redis pub/sub 채널 사용
  - 브로드캐스트 성격의 실시간 이벤트 전달

### 1.6 보호 파일 view ticket

- 목적: 보호 파일 조회용 ticket 저장
- 저장소
  - `FileViewTicketStore`
- 특징
  - `RESOURCE_VIEW` 채널
  - ticket 값은 fileId scalar payload
  - TTL 동안 재사용 가능

### 1.7 게시글 조회수 dedupe

- 목적: 동일 사용자/익명 식별자의 24시간 내 중복 조회 완화
- 저장소
  - `ArticleViewDedupeStore`
- 키 예시
  - `article:view:dedupe:v1:{articleId}:{viewerKey}`
- 특징
  - 현재는 후보가 아니라 실제 운영 중
  - Redis 실패 시 조회수 증가는 생략

### 1.8 게시글 트렌딩 점수

- 목적: 조회/댓글/반응/북마크 기반 시간 버킷 랭킹 유지
- 저장소
  - `ArticleTrendingStore`
- 키 예시
  - `trend:article:hour:{yyyyMMddHH}`
  - `trend:article:day:{yyyyMMdd}`
  - `trend:article:week:{YYYYww}`
- 자료구조
  - ZSET
- 특징
  - 현재는 후보가 아니라 실제 운영 중
  - Redis 조회 실패 시 빈 결과로 degraded 가능

### 1.9 콘텐츠 시세 시계열 캐시

- 목적: 시세 차트/히스토리 응답 캐시
- 저장소
  - `ContentMarketSeriesCacheStore`
- 특징
  - instrument + period 조합 캐시
  - TTL 기반 읽기 캐시

### 1.10 업로드 세션

- 목적: presigned 업로드 세션 상태 저장
- 저장소
  - `UploadSessionRedisStore`
- 특징
  - 업로드 토큰 기반 상태 저장
  - complete/cancel 흐름의 기준 상태

### 1.11 업로드 orphan tracker

- 목적: 완료되지 않은 업로드 오브젝트 정리 대상 추적
- 저장소
  - `UploadOrphanTrackerRedisStore`
- 특징
  - ZSET + token 메타키 조합
  - 만료 스캔 기반 정리

### 1.12 스토리지 삭제 재시도 큐 / DLQ

- 목적: 오브젝트 스토리지 삭제 실패 시 재시도와 DLQ 보관
- 저장소
  - `StorageDeleteRetryQueueStore`
- 특징
  - retry queue: ZSET + job payload
  - dead letter queue도 Redis에 유지

## 2. 적용 원칙

- TTL이 필요한 세션성 데이터는 Redis에 둔다.
- 브라우저 직접 요청을 위한 ticket 같은 보조 credential은 Redis에 둔다.
- DB 정합성이 우선인 숫자/정본 데이터는 Redis를 보조 계층으로만 사용한다.
- Redis 장애를 전파하기보다, 서비스 계층에서 degraded 또는 fallback 전략을 둔다.

## 3. 과거 후보 중 현재는 적용 완료된 것

아래 항목은 더 이상 “후보”가 아니다.

- 조회수 중복 방지
- 인기글/트렌딩 랭킹

즉, 예전 문서에서 후보로 적어두었던 조회수 dedupe와 ZSET 랭킹은 현재 실제 구현이다.

## 4. 아직 후보로 남아 있는 것

### 4.1 알림 미읽음 카운트 캐시

- 목적: 상단 배지/마이페이지 알림 카운트 빠른 표시
- 후보 키: `noti:unread:{userId}`
- 고려사항
  - 음수 방지
  - DB 재계산 폴백
  - 알림 읽음/삭제와의 동기화

### 4.2 레이트 리밋

- 목적: 로그인/댓글/글쓰기/업로드 폭주 방지
- 후보 키: `rate:{action}:{subject}`
- 고려사항
  - 사용자/익명 기준 분리
  - 운영 환경에서 설정값 외부화

### 4.3 검색 자동완성 캐시

- 목적: 핸들/슬러그 prefix 검색 응답 최적화
- 후보 키 예시
  - `autocomplete:handle:{prefix}`
  - `autocomplete:slug:{prefix}`
- 고려사항
  - 무효화 기준
  - 현재 검색은 FTS + pg_trgm 조합이라 필요성이 충분한지 검토 필요

### 4.4 작성 중 드래프트 저장

- 목적: 편집 중 임시 저장
- 후보 키 예시
  - `draft:{userId}:{boardId}`
- 고려사항
  - 프론트 편집기와 저장 규약 먼저 필요
  - 저장 충돌/복구 UX 정의 필요

## 5. 우선순위 메모

현재 시점에서 새 Redis 도입 우선순위는 대략 아래 순서가 적절하다.

1. 레이트 리밋
2. 알림 미읽음 카운트 캐시
3. 검색 자동완성
4. 드래프트 저장

조회수 dedupe와 트렌딩 랭킹은 이미 운영 중이므로 우선순위 후보 목록에서 제외한다.

## 6. 참고 파일

- `mocktalkback/src/main/java/com/mocktalkback/global/auth/jwt/RefreshTokenService.java`
- `mocktalkback/src/main/java/com/mocktalkback/global/auth/oauth2/OAuth2CodeService.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/realtime/service/NotificationPresenceService.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/realtime/service/NotificationPresenceRedisStore.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/realtime/service/NotificationRealtimeTicketStore.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/realtime/service/RealtimeRedisPublisher.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/file/service/FileViewTicketStore.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/article/service/ArticleViewDedupeStore.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/article/service/ArticleTrendingStore.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/content/service/ContentMarketSeriesCacheStore.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/file/upload/service/UploadSessionRedisStore.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/file/upload/service/UploadOrphanTrackerRedisStore.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/file/service/StorageDeleteRetryQueueStore.java`
