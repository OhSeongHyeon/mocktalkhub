# 게시판/게시글 가시성 정책

## 목적
- 홈 노출, 검색/탐색 노출, 게시판 접근, 게시글 읽기 권한을 단계적으로 정리한다.
- BoardVisibility(게시판 범위)와 ContentVisibility(게시글 범위)의 조합 규칙을 명확히 한다.

## 용어 정의
- **H 홈 노출(Home Exposure)**: 홈 화면의 공개 섹션에서 보이는 상태
- **A 탐색 노출(Discovery Exposure)**: 커뮤니티 목록/검색에서 보이는 상태
- **B 접근(Access)**: 게시판 화면(게시글 목록)으로 진입 가능한 상태
- **C 읽기(Read)**: 게시글 목록/본문을 실제로 볼 수 있는 상태

## 화면별 정책 원칙
- 홈(`/`)은 공개 콘텐츠 중심 랜딩 화면으로 본다.
- 커뮤니티(`/boards`)와 통합검색(`/search`)은 접근 가능한 대상을 찾는 탐색 도구로 본다.
- 따라서 홈과 검색/커뮤니티는 서로 다른 노출 정책을 가질 수 있다.
- 이 문서에서 `H`는 홈 정책, `A/B/C`는 탐색 및 접근 정책으로 구분한다.

## 사용자 분류 및 우선순위
- **관리자 우선권**: `RoleNames.MANAGER`, `RoleNames.ADMIN`은 모든 BoardVisibility에 접근 가능
- **보드 멤버 역할**: `BoardRole.OWNER`, `BoardRole.MODERATOR`, `BoardRole.MEMBER`, `BoardRole.BANNED`
- **차단 우선**: `BoardRole.BANNED`는 항상 차단(관리자 제외)

## 확정 정책
### 1) 홈 노출 기준(H)
| BoardVisibility | H 홈 노출(커뮤니티 목록) | 비고 |
| --- | --- | --- |
| PUBLIC | 노출 | 홈 공개 커뮤니티 대상 |
| GROUP | 미노출 | 상세 탐색은 `/boards`, `/search`에서 처리 |
| PRIVATE | 미노출 | 개인/운영 영역 제외 |
| UNLISTED | 미노출 | 운영자 전용 영역 제외 |

추가 규칙:
- 홈 커뮤니티 목록은 `PUBLIC`만 노출한다.
- 홈 최근 작성글은 `PUBLIC 게시판 + PUBLIC 게시글`만 노출한다.
- 홈 최근 작성글에서는 공지글을 제외한다.
- 홈에서는 운영성 게시판 `notice`, `inquiry`를 제외한다.
- 홈의 구독 목록은 예외적으로 "내가 접근 가능한 내가 구독한 게시판"을 노출한다.

### 2) BoardVisibility 기준(A/B)
| BoardVisibility | A 탐색 노출(커뮤니티/검색) | B 접근(게시판 화면) | 비고 |
| --- | --- | --- | --- |
| PUBLIC | 비로그인 포함 누구나 | 비로그인 포함 누구나 | 공개 커뮤니티 |
| GROUP | 로그인 사용자 | 로그인 사용자 | 비멤버도 접근 가능, 읽기는 C 기준 |
| PRIVATE | OWNER + MANAGER/ADMIN | OWNER + MANAGER/ADMIN | 비공개 커뮤니티 |
| UNLISTED | MANAGER/ADMIN | MANAGER/ADMIN | 운영자 전용 |

### 3) ContentVisibility 기준(C)
> C는 **B 접근을 통과한 사용자만** 대상으로 적용한다.

#### BoardVisibility = PUBLIC
- **PUBLIC**: 비로그인/로그인 모두
- **MEMBERS**: 로그인 사용자
- **MODERATORS**: `BoardRole.OWNER`, `BoardRole.MODERATOR`
- **ADMINS**: `RoleNames.MANAGER`, `RoleNames.ADMIN`

#### BoardVisibility = GROUP
- **PUBLIC**: 로그인 사용자(비멤버 포함)
- **MEMBERS**: 보드 멤버(`BoardRole.MEMBER` 이상, BANNED 제외)
- **MODERATORS**: `BoardRole.OWNER`, `BoardRole.MODERATOR`
- **ADMINS**: `RoleNames.MANAGER`, `RoleNames.ADMIN`

#### BoardVisibility = PRIVATE
- **PUBLIC / MEMBERS / MODERATORS**: `BoardRole.OWNER`만
- **ADMINS**: `RoleNames.MANAGER`, `RoleNames.ADMIN`

#### BoardVisibility = UNLISTED
- **모든 ContentVisibility**: `RoleNames.MANAGER`, `RoleNames.ADMIN`만

## 공지글 정책
- 공지글은 **별도 고정 영역**으로 제공한다.
- 고정 영역은 **1페이지에서만 노출**한다.
- 고정 개수는 **최대 5개**로 제한한다.
- 일반 게시글은 별도 페이징 목록으로 제공한다.
- 홈 최근 작성글에서는 공지글을 노출하지 않는다.

## 접근 불가 응답 기준
- **A/B 단계에서 차단**(노출/접근 불가): 404
- **C 단계에서 차단**(게시글 읽기 불가): 403

## 게시글 목록 API 경로
- `GET /api/boards/{id}/articles`

## 슬러그 저장 규칙(주의)
- `slug`는 **경로 전체가 아닌 세그먼트만 저장**한다. 예: `notice`, `inquiry`
- `/b/notice`, `/boards/notice`처럼 **경로 형태는 금지**한다.
- 프론트 라우트는 `/b/{slug}`로 조합하고, 백엔드 조회는 `/api/boards/slug/{slug}`를 사용한다.
- 시드/운영 데이터에 경로가 들어가면 라우팅이 깨지므로, 입력 단계에서 정규화하거나 DB 값을 정리한다.

## 참고: 구현 상태
- 본 정책 기준으로 백엔드/프론트 로직을 맞춘 상태다.
- 단, 홈 개편 이후 `H 홈 노출`은 `A 탐색 노출`보다 더 보수적인 `PUBLIC` 기준을 사용한다.
