# Ticket Redis 직렬화 표준

## 문서 목적
- 현재 백엔드에는 `알림 SSE ticket`, `보호 파일 view ticket` 두 종류의 ticket이 Redis에 저장된다.
- 이 문서는 현재 구현 기준으로 Redis key/value/TTL 규칙을 정리하고, 이후 ticket이 늘어나도 저장 포맷과 naming이 흔들리지 않게 하는 기준을 정의한다.

## 현재 적용 범위
- `NotificationRealtimeTicketStore`
- `FileViewTicketStore`

## 현재 구현 요약

### 공통점
- `StringRedisTemplate` 기반
- Redis key TTL이 ticket 유효 시간의 단일 기준
- DB 영속화 없음
- domain service는 유지하고, Redis 저장 규칙만 최소 공통화함

### 차이점
- `SSE ticket`
  - mode: `ONE_TIME`
  - value: `userId`
  - 사용 방식: `getAndDelete`
- `file view ticket`
  - mode: `TTL_REUSABLE`
  - value: `fileId`
  - 사용 방식: `get + getExpire`
  - 조회 결과는 `fileId + remainingTtl` 형태로 조합된다

## Key 규칙

### 현재 표준
- 패턴:
  - `ticket:{channel}:{ticketId}`

### 공통 enum channel 값
- `realtime_connect`
- `resource_view`
- `resource_download`

### 현재 store가 실제 사용하는 channel
- `realtime_connect`
- `resource_view`

### 현재 구현 예시
- `ticket:realtime_connect:rt_ntf_xxx`
- `ticket:resource_view:fv_xxx`

### 구현 위치
- [TicketRedisKeyBuilder.java](/D:/MyProject/mocktalk-workspace/mocktalkback/src/main/java/com/mocktalkback/global/auth/ticket/TicketRedisKeyBuilder.java)
- [TicketChannel.java](/D:/MyProject/mocktalk-workspace/mocktalkback/src/main/java/com/mocktalkback/global/auth/ticket/TicketChannel.java)

## Value 직렬화 규칙

### 현재 1차 표준
- value는 `String` 기반 scalar payload를 유지한다.
- 현재 구현:
  - SSE: `userId`
  - file view: `fileId`

### 현재 binding 방식
- SSE ticket
  - `userId`를 저장하고 consume 시 인증 컨텍스트를 복원한다.
- file view ticket
  - `fileId`를 저장하고 검증 시 path의 `fileId`와 일치 여부를 확인한다.
  - 남은 TTL은 Redis key TTL에서 읽는다.
  - 사용자 권한은 발급 시점에 `FileAccessDecisionService`가 먼저 확인한다.

### 이유
- 현재 payload가 작고 단순하다.
- ticket 종류가 아직 많지 않다.
- `StringRedisTemplate`과 잘 맞는다.

### 다음 확장 기준
- subject/resource/mode/variant 같은 메타를 `검증 시 직접 복원해야 하는 상황`이 생길 때만 아래 포맷으로 확장한다.
```text
subjectId=55|resourceId=203|mode=TTL_REUSABLE|variant=medium
```

### 지금 당장 하지 않는 것
- JSON 직렬화
- Redis Hash 전환

## TTL 규칙

### 공통 원칙
- Redis key TTL이 source of truth다.
- payload 안에 `expiresAt`를 중복 저장하지 않는다.

### mode별 규칙
- `ONE_TIME`
  - consume 성공 시 key 삭제
- `TTL_REUSABLE`
  - key 유지
  - 남은 TTL을 읽어 검증

## Store API naming 규칙

### ONE_TIME
- `save(ticket, subjectId, ttl)`
- `consume(ticket)`

### TTL_REUSABLE
- `save(ticket, resourceId, ttl)`
- `find(ticket)`

### 현재 구현 매핑
- [NotificationRealtimeTicketStore.java](/D:/MyProject/mocktalk-workspace/mocktalkback/src/main/java/com/mocktalkback/domain/realtime/service/NotificationRealtimeTicketStore.java)
  - `save`
  - `consume`
- [FileViewTicketStore.java](/D:/MyProject/mocktalk-workspace/mocktalkback/src/main/java/com/mocktalkback/domain/file/service/FileViewTicketStore.java)
  - `save`
  - `find`

## Ticket ID 규칙

### 현재 표준
- prefix + UUID

### 현재 구현
- SSE:
  - `rt_ntf_ + UUID`
- file view:
  - `fv_ + UUID`

### 구현 위치
- [TicketIdGenerator.java](/D:/MyProject/mocktalk-workspace/mocktalkback/src/main/java/com/mocktalkback/global/auth/ticket/TicketIdGenerator.java)

## 현재 기준 설계 결론
- 1차 최소 공통화는 완료됐다.
- 현재 프로젝트는 아래 조합을 유지하는 것이 맞다.
  - key naming 공통화
  - ticket id 생성 규칙 공통화
  - value는 domain별 scalar payload 유지
  - service 오케스트레이션은 domain별 유지

## 다음 확장 시 체크리스트
- 새 ticket은 `TicketChannel`로 분류됐는가
- mode가 `ONE_TIME / TTL_REUSABLE` 중 하나로 명확한가
- Redis key는 `ticket:{channel}:{ticketId}` 규칙을 따르는가
- value는 scalar string으로 충분한가
- scalar가 부족할 때만 경량 key-value payload로 확장하는가
