# 인증/인가 아키텍처 재구조화 문서

## 문서 목적
- 현재 프로젝트의 인증/인가 구조를 다시 정리하고, 왜 재설계 논의가 필요한지 명확히 설명한다.
- 기존 구조의 장점은 유지하면서도, 채널별 인증 특성 차이 때문에 드러난 한계와 개선 방향을 정리한다.
- 이 문서는 구현 계획서가 아니라 `인증/인가 철학 v2`를 정리하는 상위 설계 문서다.

## 현안건 주제
- 현재 프로젝트는 일반 API 요청에 대해서는 비교적 일관된 인증/인가 철학을 갖고 있다.
- 하지만 브라우저 네이티브 요청과 실시간 연결처럼 일반 API와 다른 성격의 채널이 늘어나면서, 기존 인증/인가 전략만으로는 운영/UX/구조 측면의 마찰이 커지고 있다.
- 대표 사례:
  - 알림 SSE 연결
  - 보호 파일 조회
  - presigned URL과 프록시 host 정합성 문제
  - 브라우저 리소스 요청에서의 Bearer 재활용 한계

즉, 지금 논점은 단순 기능 추가가 아니라 `현재 인증/인가 철학이 어디까지 유효하고, 어디서부터 재설계가 필요한가`다.

## 현설계의 설명

### 1. 기본 인증 철학
- 일반 API 인증:
  - `Authorization: Bearer <accessToken>`
  - Access Token은 프론트 메모리 저장
- 세션 재발급:
  - Refresh Token은 HttpOnly Cookie
  - Redis 기반 회전/절대 만료 관리
- 일반 API는 Stateless를 유지

### 2. 현재 특수 채널 처리 방식
- `SSE`
  - `REALTIME_CONNECT` ticket을 발급해 연결 게이트로 사용
- `보호 파일 조회`
  - `RESOURCE_VIEW` ticket을 발급해 보호 파일 view 게이트로 사용

### 3. 현재 구조의 핵심 의도
- 일반 API 인증 철학을 유지한다.
- 브라우저가 Bearer 헤더를 직접 재활용하기 어려운 채널만 보조 credential(ticket)로 감싼다.
- 도메인 인가는 ticket이 아니라 각 도메인 서비스/정책이 판단한다.

## 현설계의 장점
- 일반 API 인증 철학이 단순하다.
- refresh를 HttpOnly Cookie로 분리해 JS 노출 범위를 제한한다.
- SSE, 파일 조회처럼 예외 채널만 별도 게이트로 분리할 수 있다.
- 도메인 인가 판단을 중앙 인증 계층이 아닌 도메인 가까이에 둘 수 있다.
- 현재 규모의 프로젝트에서는 빠르게 문제를 풀 수 있다.

## 현설계의 한계점

### 1. 하나의 인증 철학이 모든 채널을 자연스럽게 커버하지 못한다
- `Bearer access token in memory`는 일반 API에는 잘 맞는다.
- 하지만 아래 채널에는 구조적으로 맞지 않는다.
  - `EventSource`
  - `<img>`, `<video>`, 새 탭 열기, 저장
  - 브라우저 재시도/프리로드

### 2. ticket 방식의 운영 부담이 커진다
- 채널이 늘어날수록 ticket 종류도 늘어날 수 있다.
- 예:
  - SSE ticket
  - file view ticket
  - 이후 download/export/embed ticket 가능성
- 문서 규칙만으로 관리하면 시간이 지날수록 느슨해질 위험이 있다.

### 3. 외부 인프라 정합성에 민감하다
- presigned URL, proxy host, Cloudflare tunnel, Nginx rewrite가 조금만 어긋나도 장애가 난다.
- 특히 객체스토리지처럼 브라우저/프록시/스토리지 3자 경계가 있는 채널은 운영 난이도가 높다.

### 4. UX 비용이 발생한다
- 보호 파일 조회는 ticket 발급 단계가 추가된다.
- 브라우저 기본 동작과 어긋나면 깜빡임, 지연, 재시도 실패 같은 UX 문제가 생길 수 있다.

### 5. 패키지 구조상 경계가 코드에 충분히 드러나지 않는다
- 현재도 `global/auth`, `domain/*`는 분리돼 있지만,
- 인증 게이트, 채널 게이트, 도메인 인가 정책의 경계가 코드 구조에 명시적으로 드러나지 않는다.

## 한계점 극복 전략 및 목표

## 목표
- 일반 API와 브라우저 특수 채널을 같은 방식으로 다루려는 시도를 멈춘다.
- `하나의 credential 전략`이 아니라 `하나의 신원 모델 + 채널별 인증 게이트`로 전환한다.
- 인증(AuthN)과 인가(AuthZ)를 구조적으로 더 분리한다.
- 모놀리스 내부에서도 책임이 보이는 구조를 만든다.

## 극복 전략

### 1. 채널별 인증 게이트를 정식 개념으로 승격
- `API`
- `REALTIME`
- `MEDIA / FILE`

이 셋은 인증 전략이 달라도 된다.

### 2. 도메인 인가를 중앙화하지 않는다
- 게시판/게시글/파일 접근 여부는 도메인 정책이 판단한다.
- 중앙 게이트는 사용자 신원과 채널 credential만 다룬다.

### 3. ticket은 “예외처리”가 아니라 “채널 게이트 구현체”로 재정의
- ticket은 유지할 수 있다.
- 다만 ad-hoc 예외가 아니라 채널 게이트의 정식 구현으로 다뤄야 한다.

### 4. 물리 분리보다 논리 분리를 먼저
- 지금 당장 인증 게이트웨이를 별도 서비스로 떼는 것보다,
- 모놀리스 내부에서 인증 게이트 계층을 분명히 만드는 것이 우선이다.

## 재수립된 인증/인가 철학 및 대원칙

### 대원칙 1. 사용자 신원 모델은 단일하게 유지한다
- 사용자의 신원은 여전히 access token / refresh token 체계로 유지한다.
- 채널별 게이트는 이 신원을 보조적으로 전달하는 수단이지, 별도 사용자 모델이 아니다.

### 대원칙 2. 인증과 인가를 분리한다
- 인증(AuthN):
  - 누구인지 확인
  - 어떤 채널 게이트를 통과했는지 확인
- 인가(AuthZ):
  - 무엇을 할 수 있는지 판단
  - 리소스 도메인이 책임진다

### 대원칙 3. 채널별 전략은 달라도 상위 원칙은 같아야 한다
- API는 Bearer
- realtime은 connect gate
- media는 media/file gate

채널별 credential이 달라도 아래 원칙은 고정한다.
- 사용자 신원은 동일
- 도메인 인가가 최종 판단
- channel credential은 짧은 수명
- 최소 권한만 부여

### 대원칙 4. 중앙화할 것은 인증, 분산할 것은 인가
- 인증은 `global/auth` 계층에서 중앙화한다.
- 인가는 `domain/*/policy`로 분산 유지한다.

### 대원칙 5. 물리적 분리는 마지막 단계다
- 먼저 논리적으로 게이트를 분리한다.
- 그 다음에야 운영/규모/조직 요구가 있을 때 물리 분리를 검토한다.

## 인증/인가 설계안

### 1. 목표 구조

```text
global/
  auth/
    principal/
    jwt/
    ticket/
    channel/
      api/
      realtime/
      media/

domain/
  board/
    policy/
    service/
    entity/
    repository/
  article/
    policy/
    service/
    entity/
    repository/
  file/
    policy/
    service/
    entity/
    repository/
  notification/
    policy/
    service/
    entity/
    repository/
```

### 2. 인증(AuthN) 계층

#### `global/auth/jwt`
- 일반 API Bearer 검증
- refresh 회전
- principal 구성

#### `global/auth/ticket`
- ticket 공통 규격
- channel / mode / key naming / id generation
- 개별 channel 구현이 재사용할 최소 공통 인프라

#### `global/auth/channel/api`
- 일반 API 요청용 인증 게이트

#### `global/auth/channel/realtime`
- SSE / WebSocket handshake용 인증 게이트
- 예: `REALTIME_CONNECT`

#### `global/auth/channel/media`
- 보호 파일 조회/다운로드용 인증 게이트
- 예: `RESOURCE_VIEW`, `RESOURCE_DOWNLOAD`

### 3. 인가(AuthZ) 계층

#### `domain/board/policy`
- 게시판 visibility
- 멤버십
- owner/moderator/admin 판정

#### `domain/article/policy`
- 게시글 공개 범위
- 게시판 접근과 글 공개 범위의 조합 판정

#### `domain/file/policy`
- 파일 귀속 자원 따라가기
- 게시글/게시판/사용자 자산의 최종 접근 판정

#### `domain/notification/policy`
- 누구에게 알림을 발송할지
- 자기 자신 제외
- 구독/카테고리/알림 설정 기반 수신 판정

### 4. 권장 요청 흐름

#### 일반 API
1. API gateway가 Bearer 검증
2. principal 구성
3. 도메인 서비스 진입
4. 도메인 policy가 인가 판단

#### realtime
1. 일반 API 인증을 거쳐 connect ticket 발급
2. realtime gateway가 ticket 검증
3. principal 구성
4. 도메인 정책 또는 realtime 서비스 진입

#### media/file
1. 일반 API 인증을 거쳐 media ticket 발급
2. media gateway가 ticket 검증
3. 파일 귀속 리소스 기준 도메인 인가 확인
4. 저장소 presigned URL 또는 proxy 응답

## 역할 및 책임

### `global/auth`
- 사용자 신원 확정
- 채널별 credential 검증
- principal 생성
- 도메인 인가에 필요한 최소 사용자 컨텍스트 제공

### `domain/*/policy`
- 리소스 접근 권한 판단
- 채널과 무관한 비즈니스 인가 규칙 유지
- visibility, membership, ownership 같은 도메인 문맥 관리

### `domain/*/service`
- use case 오케스트레이션
- policy 호출
- repository 조합

### `infra`
- Redis, Object Storage, 외부 OAuth provider 같은 구현 의존성 담당
- 인증/인가 정책 자체를 결정하지 않는다

## 해야할 것
- 인증(AuthN)과 인가(AuthZ)를 문서와 코드에서 분리한다.
- 채널별 게이트를 명시적 패키지와 이름으로 드러낸다.
- 도메인 접근 정책은 `policy` 계층으로 모은다.
- ticket은 공통 프레임워크가 아니라 최소 공통 규격으로만 관리한다.
- 브라우저 네이티브 채널은 별도 채널 게이트로 본다.
- 운영 문서에 `OCI vs Termux` 같은 인프라별 차이를 남긴다.
- 메트릭과 로그를 넣어 ticket 발급/검증 실패를 관측 가능하게 한다.

## 하지 말아야 할 것
- 모든 채널을 하나의 Bearer 전략으로 억지로 통일하려 하지 않는다.
- 중앙 게이트에서 게시판/게시글/파일 인가까지 다 판단하지 않는다.
- `AbstractTicketService` 같은 과한 범용 프레임워크를 서둘러 만들지 않는다.
- 도메인 policy를 controller/filter에 직접 흩뿌리지 않는다.
- 브라우저 직접 요청 채널에 access token query parameter를 다시 허용하지 않는다.
- 물리 분리(MSA/게이트웨이 서비스화)를 너무 일찍 시작하지 않는다.

## 단계적 전환 방향

### 1단계
- 현재 구조를 문서 기준으로 재정렬
- `global/auth/channel/*`
- `domain/*/policy`

### 2단계
- 기존 ticket / file access / realtime access 로직을 패키지 경계에 맞게 이동
- controller/service/filter에서 직접 판단하던 권한 로직을 policy 호출로 정리

### 3단계
- 채널별 메트릭, 에러 규약, 운영 가이드 정리
- media/realtime 규모가 커지면 별도 게이트 서비스 분리 검토

## 결론
- 현재 구조는 현재까지는 합리적인 해법이었다.
- 하지만 채널이 늘어나면서 `하나의 credential 전략`으로 버티는 방식의 한계가 드러나고 있다.
- 앞으로의 방향은 `현재 철학을 버리는 것`이 아니라,
  - `사용자 신원 모델은 유지`
  - `채널별 인증 게이트를 정식 구조로 승격`
  - `도메인 인가는 명시적 policy 계층으로 분리`
하는 쪽이다.

이 문서는 그 전환을 위한 기준 문서다.
