# DB 및 저장소 모델 초안

## 방향

- 기존 `tb_users`를 최대한 유지하면서 필요한 인증 보조 테이블만 추가한다.
- 토큰 원문은 저장하지 않고 해시만 저장한다.
- 운영 로그와 정리 배치를 고려해 `expires_at`, `consumed_at`, `revoked_at`를 명확히 둔다.

## 기존 테이블 활용

### `tb_users`

- 유지 컬럼
  - `email`
  - `pw_hash`
  - `is_email_verified`
  - `is_enabled`
  - `is_locked`
  - `deleted_at`
- 권장 추가 검토 컬럼
  - `password_changed_at`
  - 또는 `auth_version`

### 설계 메모

- 이메일 미인증 여부는 `is_email_verified`로 판별한다.
- 관리자 차단은 `is_enabled`, `is_locked`로 유지한다.
- 장기적으로 `user_name`의 의미 정리가 필요하다.

## 신규 테이블 제안

### 1. `tb_email_verification_tokens`

| 컬럼 | 설명 |
| --- | --- |
| `email_verification_token_id` | PK |
| `user_id` | 사용자 FK |
| `email` | 발급 당시 이메일 스냅샷 |
| `purpose` | `SIGNUP`, `EMAIL_CHANGE` |
| `token_hash` | 토큰 해시 |
| `expires_at` | 만료 시각 |
| `consumed_at` | 사용 시각 |
| `revoked_at` | 무효화 시각 |
| `created_at` | 생성 시각 |

#### 권장 인덱스

- `pk_tb_email_verification_tokens`
- `ix_tb_email_verification_tokens_user_id`
- `uq_tb_email_verification_tokens_token_hash`
- `ix_tb_email_verification_tokens_expires_at`

### 2. `tb_password_reset_tokens`

| 컬럼 | 설명 |
| --- | --- |
| `password_reset_token_id` | PK |
| `user_id` | 사용자 FK |
| `email` | 발급 당시 이메일 스냅샷 |
| `token_hash` | 토큰 해시 |
| `expires_at` | 만료 시각 |
| `consumed_at` | 사용 시각 |
| `revoked_at` | 무효화 시각 |
| `created_at` | 생성 시각 |

#### 권장 인덱스

- `pk_tb_password_reset_tokens`
- `ix_tb_password_reset_tokens_user_id`
- `uq_tb_password_reset_tokens_token_hash`
- `ix_tb_password_reset_tokens_expires_at`

### 3. `tb_user_terms_consents`

| 컬럼 | 설명 |
| --- | --- |
| `user_terms_consent_id` | PK |
| `user_id` | 사용자 FK |
| `terms_type` | `TERMS_OF_SERVICE`, `PRIVACY_POLICY`, `MARKETING` |
| `terms_version` | 문서 버전 |
| `required` | 필수 여부 |
| `agreed` | 동의 여부 |
| `agreed_at` | 동의 시각 |
| `created_at` | 생성 시각 |

#### 권장 인덱스

- `pk_tb_user_terms_consents`
- `ix_tb_user_terms_consents_user_id`
- `ix_tb_user_terms_consents_terms_type`

## Redis 설계 권장

### 기존

- Refresh Token 회전 키
  - `rt:sid:{sid}`
  - `rt:sid:abs:{sid}`

### 추가 권장

- 사용자 세션 인덱스
  - `rt:user:{userId}:sids`
- rate limit 키 예시
  - `auth:rl:email-verify:resend:email:{normalizedEmail}`
  - `auth:rl:email-verify:resend:ip:{ip}`
  - `auth:rl:password-reset:request:email:{normalizedEmail}`
  - `auth:rl:password-reset:request:ip:{ip}`

## 정리 배치 권장

- 만료된 이메일 인증 토큰 삭제
- 만료된 비밀번호 재설정 토큰 삭제
- 장기 미인증 계정 정리
- 오래된 동의 이력은 삭제하지 않고 유지 여부를 별도 정책으로 결정

## 마이그레이션 순서 제안

1. 인증/재설정/동의 이력 테이블 추가
2. 필요 시 `tb_users` 보조 컬럼 추가
3. 인덱스 추가
4. 배치 또는 스케줄러 추가
5. 초기 약관 버전 데이터 반영
