# Moderation 패키지 문서

이 문서는 `domain/moderation` 패키지와 인접 관리자 서비스의 현재 API/정책을 정리합니다.

## 1. 범위

현재 moderation 영역은 아래 기능을 포함한다.

- 사이트 관리자 사용자 관리
- 사이트 관리자 게시판 관리
- 사이트 관리자 신고/제재/감사 로그
- 커뮤니티 관리자 설정/멤버/콘텐츠/신고/제재
- 일반 사용자 신고 접수
- 제재 상태 확인을 위한 공통 `SanctionGuard`

## 2. 인증 / 권한

- 인증 방식: `Authorization: Bearer <accessToken>`
- 사이트 관리자 API(`/api/admin/**`)
  - 실제 기준: `ADMIN` 전용
- 커뮤니티 관리자 API(`/api/boards/{boardId}/admin/**`)
  - 실제 기준: `ADMIN` 또는 해당 게시판 `OWNER`/`MODERATOR`
- 신고 접수(`/api/reports`)
  - 인증 필요

중요:

- 사이트 관리자 API는 `MANAGER` 까지 허용하는 구조가 아니다.
- 게시판 관리자 권한 판정은 `BoardAdminPermissionGuard` 가 담당한다.

## 3. 공통 응답 / 페이징

- 공통 응답: `ApiEnvelope`
- 페이징 응답: `PageResponse`
- 기본 페이지: `page=0`, `size=10`
- 최대 페이지 크기: `size <= 50`

## 4. 신고 / 제재 흐름

### 신고 접수

- 엔드포인트: `POST /api/reports`
- 대상: `ARTICLE`, `COMMENT`, `USER`, `BOARD`
- 중복 제한
  - 같은 신고자 + 같은 대상 + `PENDING/IN_REVIEW` 상태 신고가 있으면 재신고 불가
- 쿨다운
  - 같은 신고자 + 같은 대상에 대해 최근 24시간 내 `RESOLVED/REJECTED` 이력이 있으면 재신고 불가
- 자기 자신 신고
  - `targetType=USER` 에서 본인 신고 불가

### 신고 처리

- 사이트 관리자 또는 게시판 관리자가 상태를 변경한다.
- 처리 시 `AdminAuditLogEntity` 에 운영 로그를 남긴다.

### 제재

- 범위: `GLOBAL`, `BOARD`
- 유형: `MUTE`, `SUSPEND`, `BAN`
- 생성 시 시작/종료 시각 검증
- 해제 시 이미 해제된 제재는 재해제 불가

## 5. 사이트 관리자 API

### 5.1 사용자 관리

- `GET /api/admin/users`
  - Query: `status`, `keyword`, `page`, `size`
- `PUT /api/admin/users/{id}/lock`
- `PUT /api/admin/users/{id}/unlock`
- `PUT /api/admin/users/{id}/role`
  - Body: `{ "roleName": "ADMIN|MANAGER|WRITER|USER" }`

### 5.2 게시판 관리

- `GET /api/admin/boards`
  - Query
    - `keyword`
    - `visibility(PUBLIC|GROUP|PRIVATE|UNLISTED)`
    - `includeDeleted`
    - `sort(ASC|DESC)`
    - `sortBy(CREATED_AT|UPDATED_AT)`
    - `page`, `size`
- `POST /api/admin/boards`
  - Body: `{ boardName, slug, description, visibility }`
  - 생성자는 해당 게시판 `OWNER` 로 등록된다.
- `PUT /api/admin/boards/{boardId}`
  - Body: `{ boardName, slug, description, visibility }`
- `DELETE /api/admin/boards/{boardId}`
  - 소프트 삭제
- `DELETE /api/admin/boards/{boardId}/image`
  - 대표 이미지 삭제

주의:

- 현재 moderation 컨트롤러에는 `POST /api/admin/boards/{boardId}/image` multipart 엔드포인트가 없다.
- 대표 이미지 등록은 업로드 세션 완료 흐름에서 `AdminBoardService.completeBoardImageUpload()` 로 연결된다.

### 5.3 신고 / 제재 / 감사

- `GET /api/admin/reports`
  - Query: `status`, `page`, `size`
- `GET /api/admin/reports/{id}`
- `PUT /api/admin/reports/{id}`
  - Body: `{ status, processedNote }`
- `GET /api/admin/sanctions`
  - Query: `scopeType`, `boardId`, `page`, `size`
- `POST /api/admin/sanctions`
  - Body: `{ userId, scopeType, boardId?, sanctionType, reason, startsAt?, endsAt?, reportId? }`
- `POST /api/admin/sanctions/{id}/revoke`
  - Body: `{ revokedReason }`
- `GET /api/admin/audit-logs`
  - Query: `actionType`, `actorUserId`, `targetType`, `targetId`, `fromAt`, `toAt`, `page`, `size`

## 6. 커뮤니티 관리자 API

### 6.1 게시판 설정

- `GET /api/boards/{boardId}/admin/settings`
- `PUT /api/boards/{boardId}/admin/settings`
  - Body: `{ boardName, description, visibility, articleWritePolicy }`
- `DELETE /api/boards/{boardId}/admin/settings/image`

주의:

- 커뮤니티 설정 수정은 slug 변경을 허용하지 않는다.
- 대표 이미지 등록도 moderation 컨트롤러 multipart가 아니라 업로드 세션 완료 흐름으로 처리된다.

### 6.2 멤버 관리

- `GET /api/boards/{boardId}/admin/members`
  - Query: `status(OWNER|MODERATOR|MEMBER|PENDING|BANNED)`, `page`, `size`
- `PUT /api/boards/{boardId}/admin/members/{memberId}/approve`
  - `PENDING` 만 승인 가능
- `PUT /api/boards/{boardId}/admin/members/{memberId}/reject`
  - `PENDING` 만 거절 가능
- `PUT /api/boards/{boardId}/admin/members/{memberId}/role`
  - Body: `{ boardRole: MEMBER|MODERATOR }`
  - `PENDING`, `BANNED` 는 역할 변경 대상이 아님
  - `OWNER` 변경은 사이트 관리자만 가능
- `PUT /api/boards/{boardId}/admin/members/{memberId}/status`
  - Body: `{ boardRole: BANNED|MEMBER }`
  - `PENDING` 은 차단 불가
  - 차단 해제는 `BANNED -> MEMBER` 만 가능

### 6.3 콘텐츠 관리

- `GET /api/boards/{boardId}/admin/contents/articles`
  - Query: `reported`, `notice`, `authorId`, `page`, `size`
- `PUT /api/boards/{boardId}/admin/contents/articles/{articleId}/notice`
  - Body: `{ notice: true|false }`
- `DELETE /api/boards/{boardId}/admin/contents/articles/{articleId}`
  - 소프트 삭제
- `GET /api/boards/{boardId}/admin/contents/comments`
  - Query: `reported`, `authorId`, `page`, `size`
- `DELETE /api/boards/{boardId}/admin/contents/comments/{commentId}`
  - 소프트 삭제

특징:

- 게시글/댓글 목록은 `reported` 필터를 지원한다.
- 댓글 목록 응답은 내용 미리보기를 잘라서 반환한다.

### 6.4 신고 / 제재

- `GET /api/boards/{boardId}/admin/reports`
- `GET /api/boards/{boardId}/admin/reports/{id}`
- `PUT /api/boards/{boardId}/admin/reports/{id}`
  - Body: `{ status, processedNote }`
- `GET /api/boards/{boardId}/admin/sanctions`
- `POST /api/boards/{boardId}/admin/sanctions`
  - Body: `{ userId, scopeType=BOARD, boardId, sanctionType, reason, startsAt?, endsAt?, reportId? }`
- `POST /api/boards/{boardId}/admin/sanctions/{id}/revoke`
  - Body: `{ revokedReason }`

게시판 범위 제재 생성은 `scopeType=BOARD` 만 허용한다.

## 7. 일반 신고 API

- `POST /api/reports`
- Body: `{ targetType, targetId, reasonCode, reasonDetail? }`
- 응답: `ReportDetailResponse`

## 8. Enum 목록

- `ReportStatus`
  - `PENDING`, `IN_REVIEW`, `RESOLVED`, `REJECTED`
- `ReportTargetType`
  - `ARTICLE`, `COMMENT`, `USER`, `BOARD`
- `ReportReasonCode`
  - `SPAM`, `ABUSE`, `HATE`, `PORN`, `PERSONAL_INFO`, `COPYRIGHT`, `OTHER`
- `SanctionScopeType`
  - `GLOBAL`, `BOARD`
- `SanctionType`
  - `MUTE`, `SUSPEND`, `BAN`
- `BoardRole`
  - `OWNER`, `MODERATOR`, `MEMBER`, `PENDING`, `BANNED`
- `AdminActionType`
  - `REPORT_PROCESS`, `SANCTION_CREATE`, `SANCTION_REVOKE`
- `AdminTargetType`
  - `ARTICLE`, `COMMENT`, `USER`, `BOARD`, `REPORT`, `SANCTION`
- `AdminBoardSortBy`
  - `CREATED_AT`, `UPDATED_AT`

## 9. 구현 메모

- 운영 로그는 신고 처리/제재 등록/제재 해제 시 생성된다.
- 제재 체크는 `SanctionGuard` 로 게시글 작성, 수정, 삭제, 반응, 북마크, 댓글 작성/수정/삭제/반응에 공통 적용된다.
- moderation 컨트롤러 자체에 대표 이미지 업로드 multipart 엔드포인트는 없고, 업로드 세션 완료 흐름이 해당 서비스 메서드로 연결된다.

## 10. 참고 파일

- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/controller/AdminUserController.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/controller/AdminBoardController.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/controller/AdminModerationController.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/controller/BoardSettingsAdminController.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/controller/BoardMemberAdminController.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/controller/BoardContentAdminController.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/controller/BoardModerationController.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/controller/ReportController.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/service/ModerationService.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/moderation/policy/BoardAdminPermissionGuard.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/common/policy/SanctionGuard.java`
