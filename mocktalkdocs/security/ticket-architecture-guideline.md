# Ticket 아키텍처 공통 규격 가이드

## 문서 목적
- 현재 프로젝트는 브라우저 기본 요청과 일반 API 인증 방식의 차이 때문에 `SSE ticket`, `file view ticket` 같은 보조 credential을 사용하기 시작했다.
- 이 문서는 ticket이 케이스별로 제각각 늘어나는 것을 막기 위해 공통 설계 원칙과 규격을 정의한다.
- 목표는 `현재 모놀리식 구조`에서도 일관된 인증 게이트를 유지하고, 나중에 서비스가 커져도 재사용 가능한 기준을 만드는 것이다.

## 배경

### 왜 ticket이 필요한가
- 일반 API는 `Authorization: Bearer <accessToken>`으로 인증한다.
- 하지만 아래 채널은 Bearer를 그대로 재활용하기 어렵다.
  - `EventSource` 기반 SSE 연결
  - `<img>`, `<video>`, `<audio>` 같은 브라우저 기본 리소스 요청
  - 새 탭 열기, 이미지 저장, 브라우저 재시도 같은 native 동작

### 현재 철학
- Access Token: 메모리 Bearer
- Refresh Token: HttpOnly Cookie
- 민감 요청을 전부 쿠키 기반으로 넓히지 않는다

즉 ticket은 이 철학을 깨지 않고, 특정 전송 채널만 별도 게이트로 분리하기 위한 보조 수단이다.

## 핵심 원칙

### 1. ticket은 본 인증을 대체하지 않는다
- ticket은 access token을 대신하는 장기 자격증명이 아니다.
- 일반 API 인증을 통과한 뒤 발급되는 `짧은 수명의 channel-specific credential`이다.

### 2. ticket은 채널별로 사용한다
- API 전체를 ticket으로 감싸지 않는다.
- 브라우저 기본 요청이나 실시간 연결처럼 Bearer 재활용이 구조적으로 어려운 경계에만 사용한다.

### 3. ticket은 최소 권한으로 제한한다
- 가능한 한 아래를 모두 바인딩한다.
  - `subject`
  - `resource`
  - `channel`
  - `mode`
  - `ttl`

### 4. 인증과 인가를 분리한다
- ticket 발급 전:
  - 일반 인증을 통과해야 한다.
- ticket 검증 전/후:
  - 리소스 인가는 해당 도메인이 판단해야 한다.
- ticket은 `누가 어떤 리소스를 어떤 채널로 접근할 수 있는가`를 짧게 캡슐화할 뿐, 도메인 인가 자체를 대체하지 않는다.

### 5. access token query param은 금지한다
- ticket을 도입하는 이유 중 하나가 `query access token` 제거다.
- 따라서 ticket 경계 밖에서 access token을 URL에 넣는 방식은 허용하지 않는다.

## 적용 대상

### 현재 적용 대상
- `SSE ticket`
- `file view ticket`

### 미래 적용 후보
- `protected download ticket`
- `embed/preview ticket`
- WebSocket handshake ticket

## Ticket 분류 규칙

### channel 기준 분류
- `REALTIME_CONNECT`
  - SSE/WS handshake
- `RESOURCE_VIEW`
  - image/video/file inline view
- `RESOURCE_DOWNLOAD`
  - export, 파일 다운로드

### mode 기준 분류
- `ONE_TIME`
  - handshake 1회만 성공하면 되는 경우
  - 예: SSE connect
- `TTL_REUSABLE`
  - 짧은 TTL 안에서 같은 URL/행위를 여러 번 자연스럽게 허용해야 하는 경우
  - 예: 보호 이미지 새 탭 열기, 저장, 재시도

## Ticket 메타 모델

### 최소 필수 필드
- `ticketId`
- `subjectType`
- `subjectId`
- `channel`
- `resourceType`
- `resourceId`
- `mode`
- `issuedAt`
- `expiresAt` 또는 `ttl`

### 선택 필드
- `variant`
- `scope`
- `traceId`
- `nonce`

### 현재 프로젝트 기준 추천 예시
```text
ticketId = fv_abc123...
subjectType = USER
subjectId = 17
channel = RESOURCE_VIEW
resourceType = FILE
resourceId = 203
mode = TTL_REUSABLE
variant = medium
ttl = 120s
```

### 현재 구현에 대한 해석
- 위 메타 모델은 `개념적 기준`이다.
- 현재 구현은 이 필드를 Redis value에 전부 직렬화하지 않는다.
- 대신 channel 구분, Redis key namespace, path parameter, 발급 시 인가, 검증 로직으로 필요한 binding을 만족시킨다.

## Redis 저장 규칙

### key naming
- 패턴:
  - `ticket:{channel}:{ticketId}`
- 예:
  - `ticket:realtime_connect:rt_xxx`
  - `ticket:resource_view:fv_xxx`

### value 규칙
- 현재 1차 표준은 `String` 기반 scalar payload를 유지한다.
- 현재 구현:
  - SSE: `userId`
  - file view: `fileId`
- 나머지 binding은 아래에서 보완한다.
  - `TicketChannel`
  - 발급 시 도메인 인가
  - 검증 시 path/fileId 대조
  - Redis TTL
- scalar payload로 부족해질 때만 경량 key-value payload로 확장한다.

### TTL 규칙
- Redis TTL이 곧 ticket 유효 시간이다.
- 별도 영속 저장은 하지 않는다.

## 발급 규칙

### 공통 절차
1. 일반 인증 통과
2. 필요한 도메인 인가 확인
3. ticket payload 구성
4. Redis 저장
5. ticket 또는 ticket 포함 URL 반환

### 발급 엔드포인트 규칙
- 채널별/리소스별로 명시적으로 둔다.
- 예:
  - `POST /api/realtime/notifications/ticket`
  - `POST /api/files/{fileId}/view-ticket`

### 발급 응답 규칙
- 최소 필드:
  - `ticket` 또는 `viewUrl`
  - `expiresInSec`
- 리소스가 곧바로 URL 사용을 요구하면 `viewUrl`을 같이 주는 것이 좋다.

## 검증 규칙

### ONE_TIME
- 성공 시 즉시 consume
- 두 번째 요청부터는 실패
- 연결 handshake에 적합

### TTL_REUSABLE
- 성공 시 consume하지 않음
- 남은 TTL 동안 반복 사용 허용
- 다만 resource binding mismatch면 즉시 실패

### 공통 실패 정책
- 존재하지 않음
- 만료됨
- 리소스 불일치
- channel 오용
- subject 불일치

모두 외부에는 과도한 정보를 주지 않는 방식으로 처리한다.

## TTL 정책

### 공통 원칙
- ticket TTL은 길게 두지 않는다.
- channel 특성과 UX 요구를 함께 본다.

### 권장 기준
- `REALTIME_CONNECT`
  - `ONE_TIME`
  - 매우 짧게
  - 연결 직전 handshake용
- `RESOURCE_VIEW`
  - `TTL_REUSABLE`
  - 브라우저 재시도와 저장 동작을 감안
  - 저장소 presigned TTL을 넘지 않도록 해야 함
- `RESOURCE_DOWNLOAD`
  - `TTL_REUSABLE`
  - 다운로드 시작/재시도 시간을 고려

### 보호 파일 현재 권장 규칙
- `file view ticket TTL = OBJECT_STORAGE_PROTECTED_VIEW_EXPIRE_SECONDS`
- 실제 presigned GET TTL은 `ticket 남은 TTL 이하`로 clamp

### 현재 구현 기본값
- `REALTIME_CONNECT`
  - 설정값이 없으면 `30초`
- `RESOURCE_VIEW`
  - 설정값이 없으면 `120초`
  - 상한은 `7일`

## 응답 형식 규칙

### 기본 응답 필드
- `ticket`
- `expiresInSec`

### URL 중심 채널
- `viewUrl`
- `downloadUrl`

### 현재 프로젝트 적용 예
- realtime:
  - `ticket`, `expiresInSec`
- file view:
  - `viewUrl`, `expiresInSec`, `protectedFile`
  - 공개 파일은 `protectedFile=false`, `expiresInSec=0`
  - 보호 파일은 `ticket`이 포함된 `viewUrl`을 반환

## 서비스 구조 규칙

### 추천 레이어
- `XxxTicketService`
  - 발급
  - 검증/consume/validate
- `XxxTicketStore`
  - Redis 저장
- `Controller`
  - ticket 발급 endpoint
- `Filter` 또는 `Service`
  - 채널 특성에 맞는 검증 지점

### naming 규칙
- `issue(...)`
- `consume(...)`
- `validate(...)`
- `find(...)`

기준:
- `ONE_TIME`면 `consume`
- `TTL_REUSABLE`면 `validate`

## 보안 원칙
- ticket은 query param으로 전달될 수 있지만 access token은 아니다.
- ticket은 짧은 수명이어야 한다.
- ticket은 가능한 리소스 바인딩을 가져야 한다.
- `publicBaseUrl` 같은 우회 경로가 보호 리소스에 섞이지 않게 한다.
- 운영 로그/애플리케이션 로그에 ticket 전체값을 그대로 남기지 않도록 주의한다.

## 관찰성과 운영

### 최소 로그 항목
- ticket 발급 성공/실패
- ticket 검증 실패 유형
- resource mismatch
- 만료 비율

### 운영 지표 후보
- 발급 수
- 검증 성공률
- 만료로 인한 실패율
- channel별 ticket 사용량

## 현재 프로젝트에 대한 결론
- 지금은 `MSA 분할`보다 `ticket 공통 규격`이 우선이다.
- 인증은 중앙화할 수 있어도, 인가는 리소스 도메인 가까이에 두는 것이 맞다.
- 따라서 현재 단계의 최적 구조는 아래다.
  - 일반 API: Bearer access token
  - 특수 채널: channel-specific ticket
  - 인가 판단: 각 도메인 서비스

### 구현 원칙
- 공통화의 목표는 `규격 통일`이지 `범용 ticket 프레임워크` 구축이 아니다.
- 채널별 ticket service는 각 도메인에 남겨야 한다.
- 공통 구현이 필요하더라도 아래 수준에서 멈추는 것이 맞다.
  - enum
  - key naming
  - ticket id 생성
  - 얇은 Redis store 포트

### 피해야 할 것
- 도메인 발급/검증 흐름을 하나의 추상 서비스로 묶기
- 인가 로직을 범용 ticket validator로 끌어올리기
- 공통화 때문에 나중에 도메인 분해가 더 어려워지는 구조

## 실무 적용 체크리스트
- 새 ticket을 만들 때 channel/mode를 먼저 정했는가
- ONE_TIME인지 TTL_REUSABLE인지 명확한가
- TTL 근거가 있는가
- resource binding이 있는가
- access token query param을 우회하지 않는가
- 검증 실패 시 과도한 정보가 노출되지 않는가
- Redis key/payload 규칙을 따르는가
