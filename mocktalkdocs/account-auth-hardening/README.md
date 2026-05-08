# 계정/인증 고도화 문서

## 문서 목적

- 회원가입, 이메일 인증, 비밀번호 재설정 기능을 MVP 수준에서 운영 수준으로 고도화하기 위한 기준 문서다.
- 프론트엔드와 백엔드를 함께 다루지만, 버전관리 이력을 남기기 위해 `mocktalkback` 저장소 내부에 보관한다.
- 민감정보를 추가 수집하지 않는 방향을 전제로 한다.

## 범위

- 로컬 회원가입
- 이메일 인증
- 비밀번호 재설정
- 약관/개인정보/연령 정책
- API/DB 초안
- 구현 및 테스트 체크리스트

## 현재 구현 기준선

- 백엔드에는 `/api/auth/join`, `/api/auth/login`, `/api/auth/refresh`, `/api/auth/logout`, `/api/auth/oauth2/callback`이 구현되어 있다.
- 프론트는 `/join` 페이지에서 회원가입을 받고, `401 -> refresh -> 실패 시 logout` 흐름을 이미 사용 중이다.
- Refresh Token은 `HttpOnly Cookie`, `SameSite=Lax`, `Path=/api/auth/refresh` 및 `/api/auth/logout`으로 제한되어 있다.
- `OriginAllowlistFilter`가 `refresh`, `logout`에만 적용되어 쿠키 기반 민감 엔드포인트를 보호하고 있다.
- `tb_users.is_email_verified` 컬럼은 이미 존재하지만, 현재 로컬 회원가입은 `emailVerified=false`, `enabled=true`로 생성되고 로그인 시 이메일 인증 여부를 막지 않는다.
- 이메일 인증 발송, 인증 완료 처리, 비밀번호 재설정 요청/확정 API는 아직 없다.

## 핵심 갭

- 미인증 이메일로도 로그인 가능하다.
- 회원가입 시 약관 동의 이력 저장 구조가 없다.
- 비밀번호 재설정 기능이 없다.
- 계정 존재 여부를 숨겨야 하는 재발송/재설정 엔드포인트가 아직 없다.
- 운영용 rate limit, 토큰 만료/재발급 정책, 정리 배치가 아직 없다.

## 권장 정책 요약

- 개인정보 최소 수집: `loginId`, `email`, `password`, `displayName` 중심으로 운영한다.
- 현재 `userName`은 실명 의미를 제거하거나 선택값으로 낮추는 방향을 우선 검토한다.
- 만 14세 미만 가입은 초기 단계에서 받지 않는다.
- 로컬 계정은 이메일 인증 완료 전 로그인 불가로 전환한다.
- 이메일 인증과 비밀번호 재설정 토큰은 원문 저장 없이 해시로만 저장한다.
- 비밀번호 재설정 성공 시 모든 refresh 세션을 폐기한다.

## 문서 목록

- [signup-flow.md](./signup-flow.md)
- [email-verification.md](./email-verification.md)
- [password-reset.md](./password-reset.md)
- [terms-and-privacy.md](./terms-and-privacy.md)
- [api-design.md](./api-design.md)
- [db-model.md](./db-model.md)
- [checklist.md](./checklist.md)

## 관련 현재 코드

- `src/main/java/com/mocktalkback/domain/user/controller/AuthController.java`
- `src/main/java/com/mocktalkback/domain/user/service/AuthService.java`
- `src/main/java/com/mocktalkback/domain/user/entity/UserEntity.java`
- `src/main/java/com/mocktalkback/global/auth/CookieUtil.java`
- `src/main/java/com/mocktalkback/global/auth/OriginAllowlistFilter.java`
- `src/main/java/com/mocktalkback/global/config/SecurityConfig.java`
- `src/features/auth/api/authApi.ts`
- `src/shared/lib/http/api.ts`
- `src/pages/RegisterPage.vue`
