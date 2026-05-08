# Presigned URL 보안 점검 보고서

## 문서 목적
- 대상 문서: `docs/security/mvp-security-technical-debt.md`
- 대상 범위: presigned URL 및 오브젝트 스토리지 관련 보안 이슈
- 목적: 현재 코드 기준으로 `해결됨`, `부분 해결`, `미해결` 상태를 다시 판정한다.

## 점검 기준
- 본 보고서는 2026-03-15 현재 저장소 코드 기준 점검이다.
- 운영 환경의 실제 환경 변수 값은 확인하지 못했으므로, 설정값 의존 항목은 `부분 해결` 또는 `운영 확인 필요`로 둔다.

## 결론 요약
- 해결됨
  - presigned 업로드 URL 발급/완료 검증
  - 게시글 첨부파일 다운로드 권한 검증
  - 비공개 게시글 본문 이미지/파일의 직접 조회 우회 문제
  - raw presigned URL이 본문에 저장되는 문제
- 부분 해결
  - presigned URL 만료 시간 정책
  - `publicBaseUrl` 사용 정책
  - 오브젝트 스토리지 운영 설정 의존성
- 미해결
  - 현재 코드 기준으로 presigned URL 관련 핵심 미해결 항목은 없음

## 상세 판정

### 1. presigned 업로드 URL 무분별 발급 가능성
- 판정: 해결됨
- 근거:
  - 업로드 세션 시작 API는 인증된 사용자 기준으로 동작한다.
  - 서버가 업로드 목적, 파일명, MIME 타입, 크기를 먼저 검증한 뒤 presigned 업로드 URL을 발급한다.
  - 업로드 완료 시 `uploadToken`을 소비하고, 소유자 일치 여부와 실제 업로드된 객체 메타를 다시 검증한다.

### 2. presigned 업로드 URL의 만료 시간 부재 또는 통제 부재
- 판정: 부분 해결
- 근거:
  - presigned URL 만료 시간은 코드와 설정에 존재한다.
  - 기본값과 상한 보정도 있다.
  - 다만 상한이 여전히 `604800초(7일)`로 넓고, 운영에서 과도한 값을 넣는 것을 아주 보수적으로 막지는 않는다.

### 3. 게시글 첨부파일 다운로드가 권한 모델 밖에서 바로 열리는 문제
- 판정: 해결됨
- 근거:
  - `/api/articles/{id}/attachments/{fileId}/download`는 게시글/게시판 접근 권한 확인 후 download URL을 발급한다.
  - 즉 첨부 다운로드는 presigned URL을 쓰더라도 권한 모델 안으로 들어와 있다.

### 4. 비공개 게시글 본문 이미지/파일이 `/api/files/{id}/view`로 직접 열리는 문제
- 판정: 해결됨
- 근거:
  - `FileAccessDecisionService`가 파일 귀속과 접근 가능 여부를 판정한다.
  - `FileViewService`는 공개/보호 전달 모드를 나누고, 보호 파일은 ticket 검증을 통과해야만 presigned GET으로 리다이렉트한다.
  - 보호 파일은 `file view ticket` 없이는 브라우저 직접 조회가 불가능하다.

### 5. raw presigned URL이 본문이나 프론트 상태에 직접 저장되는 문제
- 판정: 해결됨
- 근거:
  - 본문에는 여전히 내부 `/api/files/{id}/view` 경로를 canonical URL로 저장한다.
  - 보호 파일 ticket URL은 렌더링 시점에만 사용된다.
  - 즉 presigned URL이나 ticket URL이 장기 참조 경로로 저장되는 구조는 아니다.

### 6. `publicBaseUrl` 설정으로 인한 사실상 공개 조회 우회 가능성
- 판정: 부분 해결
- 근거:
  - 보호 파일은 이제 `publicBaseUrl`을 무시하고 `resolveProtectedViewUrl`과 `/storage` 프록시를 사용한다.
  - 즉 가장 위험했던 보호 파일 우회 문제는 해소됐다.
  - 다만 공개 파일은 여전히 `publicBaseUrl`을 사용할 수 있으므로, 파일 분류가 잘못되면 운영 설정이 보안에 영향을 줄 여지는 남아 있다.

### 7. presigned URL 정책이 운영 설정에 크게 의존하는 문제
- 판정: 부분 해결
- 근거:
  - 관련 설정 키는 코드에 명시돼 있고, 보호 파일 TTL도 별도 정책을 가진다.
  - 그러나 실제 운영에서 `publicBaseUrl`, `presignExpireSeconds`, `protectedViewExpireSeconds`, `uploadProxyPrefix`를 어떤 값으로 쓰는지 저장소만으로는 확정할 수 없다.
  - 따라서 구현 경계는 좋아졌지만, 운영 보안 수준을 코드만으로 완전히 보장하진 못한다.

## 운영값 확인이 필요한 항목
- `OBJECT_STORAGE_PUBLIC_BASE_URL`
  - 공개 파일에만 의도적으로 쓰는지 확인 필요
- `OBJECT_STORAGE_PRESIGN_EXPIRE_SECONDS`
  - 업로드/다운로드 TTL이 과도하게 길지 않은지 확인 필요
- `OBJECT_STORAGE_PROTECTED_VIEW_EXPIRE_SECONDS`
  - 보호 파일 조회 TTL이 실제 운영에서 적절한지 확인 필요
- `OBJECT_STORAGE_UPLOAD_PROXY_PREFIX`
  - 프록시 경로가 외부 노출 정책과 맞는지 점검 필요
- `OBJECT_STORAGE_PRESIGN_ENDPOINT`
  - presigned URL 생성 기준 엔드포인트가 실제 공개 경계와 맞는지 점검 필요

## 최종 정리
- presigned 업로드와 첨부 다운로드는 해결된 상태다.
- 가장 위험했던 `비공개 게시글 본문 이미지/파일 직접 접근` 문제도 해결됐다.
- 현재 남은 핵심 리스크는 구현 미비라기보다 운영 설정과 파일 분류 정책에 더 가깝다.

## 후속 우선순위 제안
1. 운영 환경의 `publicBaseUrl`, TTL, 프록시 설정 점검 절차 고정
2. 공개 파일/보호 파일 분류표 유지 및 회귀 테스트 보강
3. 필요 시 presigned TTL 상한 보수화 검토
