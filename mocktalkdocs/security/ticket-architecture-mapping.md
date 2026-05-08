# Ticket 아키텍처 매핑 문서

## 문서 목적
- [ticket-architecture-guideline.md](/D:/MyProject/mocktalk-workspace/docs/security/ticket-architecture-guideline.md)의 공통 규격을 현재 구현체에 어떻게 적용하고 있는지 정리한다.
- 현재 대상은 `알림 SSE ticket`과 `보호 파일 view ticket`이다.

## 현재 ticket 목록

| ticket | channel | mode | subject | resource | 발급 목적 |
| --- | --- | --- | --- | --- | --- |
| 알림 SSE ticket | `REALTIME_CONNECT` | `ONE_TIME` | 사용자 | 알림 스트림 연결 | EventSource handshake |
| 보호 파일 view ticket | `RESOURCE_VIEW` | `TTL_REUSABLE` | 사용자 | 파일 | 보호 이미지/영상/파일 view 및 브라우저 재요청 허용 |

## 1. 알림 SSE ticket

### 역할
- `EventSource` 연결은 Authorization Bearer를 직접 싣기 어렵다.
- 따라서 stream handshake를 위한 짧은 1회용 ticket이 필요하다.

### 현재 구현 구조
- 발급:
  - `POST /api/realtime/notifications/ticket`
- 검증:
  - `/api/realtime/notifications/stream?ticket=...`
- 핵심 특성:
  - 1회용 consume
  - handshake 성공 이후에는 stream 자체가 연결 상태를 유지

### 공통 규격 매핑
- channel:
  - `REALTIME_CONNECT`
- mode:
  - `ONE_TIME`
- subject:
  - `USER`
- resource:
  - `NOTIFICATION_STREAM`

### 판단
- 현재 SSE ticket은 공통 규격과 잘 맞는다.
- 이후 WebSocket 전환이 있어도 같은 패턴을 유지할 수 있다.

## 2. 보호 파일 view ticket

### 역할
- 브라우저 `<img>`, `<video>`, 새 탭 열기, 저장 동작은 메모리 Bearer를 직접 실을 수 없다.
- 따라서 보호 파일 조회를 위한 별도 gate가 필요하다.

### 현재 구현 구조
- 발급:
  - `POST /api/files/{fileId}/view-ticket`
- 사용:
  - `/api/files/{fileId}/view?ticket=...`
- 핵심 특성:
  - 공개 파일은 ticket 없이 기존 보기 URL을 반환한다.
  - 보호 파일만 ticket 포함 보기 URL을 반환한다.
  - 짧은 TTL 동안 재사용 가능
  - 검증 후 남은 TTL 이하의 presigned GET으로 리다이렉트
  - resource binding은 `Redis의 fileId`와 `path fileId` 비교로 수행한다
  - `variant` 미지정 시 기본값은 `medium`이고, 비이미지 또는 변환본이 없으면 원본으로 fallback한다

### 공통 규격 매핑
- channel:
  - `RESOURCE_VIEW`
- mode:
  - `TTL_REUSABLE`
- subject:
  - `USER`
- resource:
  - `FILE`

### 왜 ONE_TIME가 아닌가
- 보호 이미지/영상은 아래 동작이 자연스러워야 한다.
  - 새 탭 열기
  - 다른 이름으로 저장
  - 브라우저 재시도
  - 동일 페이지 내 반복 조회
- 그래서 `1회용 consume`은 과도했고, 현재는 `TTL_REUSABLE`로 정리했다.

## 비교 정리

| 항목 | 알림 SSE ticket | 보호 파일 view ticket |
| --- | --- | --- |
| channel | `REALTIME_CONNECT` | `RESOURCE_VIEW` |
| mode | `ONE_TIME` | `TTL_REUSABLE` |
| 검증 위치 | stream 연결 시점 | `/api/files/{id}/view` |
| 검증 후 동작 | 연결 성립 | presigned GET 리다이렉트 |
| 브라우저 재요청 허용 | 불필요 | 필요 |
| TTL 특징 | 기본 `30초` | 기본 `120초`, 상한 `7일` |

## 현재 규격에서 드러난 공통 패턴

### 발급 단계
1. 일반 인증 통과
2. 도메인 인가 확인
3. Redis TTL 저장
4. ticket 또는 ticket 포함 URL 반환

### 검증 단계
1. ticket 존재 확인
2. channel 목적에 맞는 mode 적용
3. resource binding 확인
4. 실패 시 보수적으로 차단

## 앞으로 늘어날 가능성이 있는 ticket 후보

### 1. 보호 다운로드 ticket
- 예:
  - 마크다운 원문 다운로드
  - 보호 첨부 다운로드
- 추천 mode:
  - `TTL_REUSABLE`

### 2. embed/preview ticket
- 예:
  - 외부 임베드 미리보기
  - 보호 자산 preview
- 추천 mode:
  - use case에 따라 다름

### 3. WebSocket connect ticket
- SSE를 대체하거나 병행할 때
- 추천 mode:
  - `ONE_TIME`

## 구현 시 주의점

### 주의 1. ticket마다 규칙을 새로 만들지 않는다
- channel
- mode
- TTL source
- binding 필드

이 네 가지를 먼저 공통 가이드에 맞춰 정한 뒤 구현한다.

### 주의 2. 인가를 ticket 서비스에 과도하게 몰아넣지 않는다
- ticket 서비스는 발급/검증 경계다.
- 실제 리소스 인가 판단은 도메인 서비스가 해야 한다.

### 주의 3. 브라우저 기본 동작과 충돌하는지 먼저 본다
- 파일/미디어 계열은 `ONE_TIME`가 잘 안 맞는다.
- 실시간 handshake는 `ONE_TIME`가 잘 맞는다.

## 현재 결론
- `SSE ticket`과 `file view ticket`은 서로 다른 문제가 아니라, 같은 ticket 아키텍처 위의 두 구현체다.
- 차이는 주로 `channel`과 `mode`에서 발생한다.
- 따라서 앞으로 ticket이 추가되더라도 새 규칙을 만드는 방식이 아니라 아래 질문으로 분류해야 한다.
  1. 이 요청은 어떤 channel인가
  2. ONE_TIME인가 TTL_REUSABLE인가
  3. 어떤 resource binding이 필요한가
  4. TTL source는 무엇인가
