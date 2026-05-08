# API 설계 초안

## 설계 원칙

- 모든 인증 관련 API는 `/api/auth` 하위에 둔다.
- 쿠키 기반 민감 엔드포인트는 현재처럼 `refresh`, `logout`에만 제한적으로 유지한다.
- 이메일 인증, 비밀번호 재설정 요청 API는 계정 존재 여부를 숨긴다.
- 토큰 확인 API는 해시 검증과 1회용 소비를 보장한다.

## 기존 API

| 메서드 | 경로 | 상태 |
| --- | --- | --- |
| POST | `/api/auth/join` | 운영 중 |
| POST | `/api/auth/login` | 운영 중 |
| POST | `/api/auth/refresh` | 운영 중 |
| POST | `/api/auth/logout` | 운영 중 |
| POST | `/api/auth/oauth2/callback` | 운영 중 |

## 신규 API 제안

| 메서드 | 경로 | 목적 |
| --- | --- | --- |
| POST | `/api/auth/email-verifications/resend` | 가입 인증 메일 재발송 |
| POST | `/api/auth/email-verifications/confirm` | 이메일 인증 완료 |
| POST | `/api/auth/password-resets/request` | 비밀번호 재설정 요청 |
| POST | `/api/auth/password-resets/confirm` | 비밀번호 재설정 완료 |

## 로그인 응답 정책 변경

### 현재

- 자격 증명이 맞으면 이메일 인증 여부와 무관하게 로그인 가능

### 목표

- 로컬 계정이고 `is_email_verified=false`이면 토큰 미발급
- 응답:
  - HTTP `403`
  - 코드 `AUTH_EMAIL_VERIFICATION_REQUIRED`
  - 메시지 `이메일 인증 후 로그인할 수 있습니다.`

## 엔드포인트 상세

### 1. `POST /api/auth/email-verifications/resend`

#### 요청

```json
{
  "email": "user@example.com"
}
```

#### 응답

- 항상 `202 Accepted` 또는 `200 OK`
- 예시 메시지:

```json
{
  "message": "인증 메일 발송 대상이면 메일을 전송했습니다."
}
```

#### 비고

- 계정 존재 여부 비노출
- 인증 완료 계정도 동일 응답
- rate limit 필요

### 2. `POST /api/auth/email-verifications/confirm`

#### 요청

```json
{
  "token": "base64url-token"
}
```

#### 성공 응답

```json
{
  "message": "이메일 인증이 완료되었습니다."
}
```

#### 실패 응답

- `400 AUTH_EMAIL_VERIFICATION_TOKEN_INVALID`
- `400 AUTH_EMAIL_VERIFICATION_TOKEN_EXPIRED`
- `409 AUTH_EMAIL_ALREADY_VERIFIED`

### 3. `POST /api/auth/password-resets/request`

#### 요청

```json
{
  "email": "user@example.com"
}
```

#### 응답

- 항상 동일 응답

```json
{
  "message": "재설정 메일 발송 대상이면 메일을 전송했습니다."
}
```

### 4. `POST /api/auth/password-resets/confirm`

#### 요청

```json
{
  "token": "base64url-token",
  "newPassword": "new-password-value",
  "confirmPassword": "new-password-value"
}
```

#### 성공 응답

```json
{
  "message": "비밀번호가 변경되었습니다."
}
```

#### 실패 응답

- `400 AUTH_PASSWORD_RESET_TOKEN_INVALID`
- `400 AUTH_PASSWORD_RESET_TOKEN_EXPIRED`
- `400 AUTH_PASSWORD_POLICY_VIOLATION`
- `400 AUTH_PASSWORD_CONFIRM_MISMATCH`

## 프론트 라우트 권장

| 경로 | 목적 |
| --- | --- |
| `/join` | 회원가입 |
| `/verify-email` | 이메일 인증 결과 처리 |
| `/forgot-password` | 비밀번호 재설정 요청 |
| `/reset-password` | 비밀번호 재설정 완료 |

## 프론트 UX 메모

- 로그인 페이지에 `비밀번호 재설정` 링크를 추가한다.
- 미인증 로그인 응답을 받으면 재발송 버튼이 있는 안내 UI를 보여준다.
- 이메일 인증/재설정 결과 페이지는 토큰을 URL 쿼리로 받아 백엔드 확인 API를 호출한다.
