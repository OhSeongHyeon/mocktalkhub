# Mocktalk 인증/인가 설계 요약

이 문서는 현재 프로젝트의 인증/인가 구조와 흐름을 코드 기준으로 정리한 문서입니다.

## 핵심 정책

- 인증 방식: JWT Access Token
- 재발급 방식: Refresh Token + Redis 세션 회전
- Access Token 저장: 프론트 메모리 저장
- Refresh Token 저장: HttpOnly Cookie(`refresh_token`)
- Refresh 쿠키 경로: `/api/auth/refresh`, `/api/auth/logout`
- CSRF 방어: `POST /api/auth/refresh`, `POST /api/auth/logout` 에만 Origin allowlist 적용
- 일반 API: `SessionCreationPolicy.STATELESS`
- OAuth2 로그인 플로우: 세션이 필요한 경로만 `SessionCreationPolicy.IF_REQUIRED`
- 브라우저가 Bearer 헤더를 직접 붙이기 어려운 채널은 ticket 기반 게이트로 분리

## 토큰 구조와 발급

### Access Token

- 전달: `Authorization: Bearer <accessToken>`
- 주요 클레임
  - `sub`: 사용자 ID
  - `typ=access`
  - `role`
  - `authBit`
  - `iss`
  - `iat`
  - `exp`
- 만료: `JWT_ACCESS_TTL_SECONDS` 기본 3600초

### Refresh Token

- 저장 위치: HttpOnly Cookie `refresh_token`
- 같은 이름의 쿠키를 경로별로 2개 발급
  - `Path=/api/auth/refresh`
  - `Path=/api/auth/logout`
- 주요 클레임
  - `sub`
  - `typ=refresh`
  - `sid`
  - `jti`
  - `rm`
  - `iss`
  - `iat`
  - `exp`
- 만료
  - 상대 만료: `JWT_REFRESH_TTL_SECONDS` 기본 14일
  - 절대 만료: `JWT_REFRESH_ABSOLUTE_TTL_SECONDS` 기본 30일

`rememberMe=false` 인 경우에는 Max-Age 없는 세션 쿠키로 발급된다.

## Refresh 회전과 폐기

Refresh 세션 상태는 Redis에 저장한다.

- `rt:sid:<sid>` -> 현재 `jti`
- `rt:sid:abs:<sid>` -> absolute expire epoch(sec)

회전 규칙:

1. Refresh 토큰을 파싱해 `sid`, `jti`, `rm` 을 읽는다.
2. Redis Lua 스크립트(`redis/refresh_rotate.lua`)로 현재 `jti` 를 비교한다.
3. 일치하면 새 `jti` 로 교체하고 TTL을 `min(refreshTTL, remainingAbsTTL)` 로 갱신한다.
4. 불일치면 `REFRESH_INVALID`, 절대 만료 초과면 `REFRESH_EXPIRED` 로 처리한다.
5. 로그아웃은 `sid` 관련 Redis 키를 삭제하고 쿠키를 비운다.

## API 인증 흐름

### 1. 로그인

- `POST /api/auth/login`
- 응답
  - Access Token 본문 반환
  - Refresh 쿠키 2개 발급(`/refresh`, `/logout`)

### 2. 일반 API 호출

- Access Token 을 Authorization 헤더로 전달
- `JwtAuthFilter` 가 토큰을 검증하고 `SecurityContext` 를 채운다

### 3. Access 만료 후 재발급

- `POST /api/auth/refresh`
- Refresh 쿠키가 있으면 Access Token 재발급
- Refresh Token 도 함께 회전하고 쿠키 2개를 모두 갱신
- 쿠키가 없거나 무효하면 401과 함께 refresh/logout 쿠키를 정리

### 4. 로그아웃

- `POST /api/auth/logout`
- logout 경로용 Refresh 쿠키가 있으면 Redis 세션 폐기
- 쿠키가 없어도 refresh/logout 쿠키는 모두 삭제

## 특수 채널 인증 게이트

일반 API는 Bearer Access Token을 쓰고, 브라우저가 직접 여는 채널은 ticket으로 분리한다.

### 1. 알림 실시간 연결

- 발급 API: `POST /api/realtime/notifications/ticket`
- 스트림 연결: `GET /api/realtime/notifications/stream?ticket=...`
- 채널: `REALTIME_CONNECT`
- 저장소: `NotificationRealtimeTicketStore`
- 특징
  - 1회용 ticket
  - `accessToken` query parameter 특례는 제거됨
  - 검증은 `NotificationRealtimeTicketAuthFilter` 가 담당

### 2. 보호 파일 조회

- 발급 API: `POST /api/files/{fileId}/view-ticket`
- 조회 URL: `GET /api/files/{id}/view?ticket=...`
- 채널: `RESOURCE_VIEW`
- 저장소: `FileViewTicketStore`
- 특징
  - 공개 파일은 ticket 없이 기존 view URL 사용
  - 보호 파일만 ticket 사용
  - ticket은 TTL 내 재사용 가능
  - 실제 파일 응답은 남은 ticket TTL 이하의 presigned GET 으로 연결

### 3. 설계 원칙

- 일반 API 인증 철학은 계속 `Bearer access token + HttpOnly refresh cookie` 를 유지한다.
- ticket은 브라우저 전송 채널 제약을 풀기 위한 보조 credential이다.
- ticket은 도메인 인가를 대체하지 않는다.

## CSRF / Origin 정책

- 적용 대상: `POST /api/auth/refresh`, `POST /api/auth/logout`
- 검사 기준: `OriginAllowlistFilter`
- 허용 목록: `SECURITY_ORIGIN_ALLOWLIST`
- 기본값이 비어 있으면 두 엔드포인트는 403으로 차단된다.
- 모든 API에 CSRF를 강제하지는 않는다.

## OAuth2 로그인

### 흐름

1. `GET /api/oauth2/authorization/{provider}`
2. Provider 인증 후 `GET /api/login/oauth2/code/{provider}`
3. 성공 시
   - 사용자 연동/생성
   - Refresh 쿠키 2개 발급
   - Redis 1회용 코드 발급
   - `/oauth/callback?code=...` 로 리다이렉트
4. 프론트가 `POST /api/auth/oauth2/callback` 으로 코드를 교환
5. Access Token 본문 응답

### 1회용 코드

- 저장 키 prefix: `oauth:code:`
- 저장소: `OAuth2CodeService`
- 소비 방식: Redis `get + delete` 를 한 번에 수행하는 1회성 코드
- TTL: `OAUTH2_CODE_TTL_SECONDS` 기본 60초

### 프론트 콜백 계약

- 프론트 라우트: `GET /oauth/callback`
- 코드 교환 API: `POST /api/auth/oauth2/callback`
- 응답: `{ accessToken, tokenType, expiresInSec }`
- Refresh Token 은 백엔드가 HttpOnly 쿠키로 내려준다.

### 설정

- `OAUTH2_REDIRECT_PATH`
  - `application-dev.yml` 기본값: `http://localhost:5173/oauth/callback`
- `OAUTH2_REMEMBER_ME_DEFAULT`
  - 기본값: `false`

## 에러 응답

현재 백엔드는 `ApiError.code` 에 공통 코드(`COMMON_401` 등)를 내려주고, 인증/토큰 세부 사유는 `reason` 에 둔다.

주요 예시:

- `COMMON_401` + `REFRESH_INVALID`
- `COMMON_401` + `REFRESH_EXPIRED`
- `COMMON_401` + `OAUTH2_CODE_INVALID`

클라이언트는 `code` 와 `reason` 을 함께 보고 분기하는 것이 안전하다.

## 보안 체인 요약

- OAuth2 체인
  - matcher: `/api/oauth2/**`, `/api/login/oauth2/**`
  - 세션 정책: `IF_REQUIRED`
- API 체인
  - 세션 정책: `STATELESS`
  - 공개 GET
    - `/api/boards/**`
    - `/api/articles/**`
    - `/api/search/**`
    - `/api/contents/**`
    - `/api/files/*/view`
    - `/api/realtime/boards/**`

## 환경 변수 / 설정

- JWT
  - `JWT_SECRET`
  - `JWT_ISSUER`
  - `JWT_ACCESS_TTL_SECONDS`
  - `JWT_REFRESH_TTL_SECONDS`
  - `JWT_REFRESH_ABSOLUTE_TTL_SECONDS`
- 보안
  - `SECURITY_COOKIE_SECURE`
  - `SECURITY_ORIGIN_ALLOWLIST`
- OAuth2
  - `OAUTH2_CODE_TTL_SECONDS`
  - `OAUTH2_REDIRECT_PATH`
  - `OAUTH2_REMEMBER_ME_DEFAULT`

## Redis 레포지토리 스캔

Redis 레포지토리를 사용할 때는 `infra.redis` 하위만 스캔한다.

- 설정 클래스: `mocktalkback/src/main/java/com/mocktalkback/infra/redis/RedisRepositoryConfig.java`
- 스캔 범위: `com.mocktalkback.infra.redis`

## 참고 파일

- `mocktalkback/src/main/java/com/mocktalkback/global/config/SecurityConfig.java`
- `mocktalkback/src/main/java/com/mocktalkback/global/auth/CookieUtil.java`
- `mocktalkback/src/main/java/com/mocktalkback/global/auth/OriginAllowlistFilter.java`
- `mocktalkback/src/main/java/com/mocktalkback/global/auth/jwt/JwtAuthFilter.java`
- `mocktalkback/src/main/java/com/mocktalkback/global/auth/jwt/JwtTokenProvider.java`
- `mocktalkback/src/main/java/com/mocktalkback/global/auth/jwt/RefreshTokenService.java`
- `mocktalkback/src/main/java/com/mocktalkback/global/auth/oauth2/OAuth2LoginSuccessHandler.java`
- `mocktalkback/src/main/java/com/mocktalkback/global/auth/oauth2/OAuth2CodeService.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/realtime/service/NotificationRealtimeTicketStore.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/file/service/FileViewTicketStore.java`
