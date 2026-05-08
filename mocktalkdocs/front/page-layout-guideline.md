# 페이지 레이아웃 가이드라인

## 문서 목적
- 현재 프론트 공통 레이아웃 규칙과 예외를 정리한다.
- 새 페이지를 만들거나 기존 페이지를 손볼 때 따라야 할 화면 구조, 간격, 패널, 헤더 기준을 정의한다.
- 이 문서는 색상 리브랜딩 문서가 아니라 `페이지 구성 규격` 문서다.

## 현재 적용 상태

### 공통 기반
- 공통 셸: `src/widgets/layout/AppShell.vue`
- 공통 폭 컨테이너: `src/shared/ui/PageContainer.vue`
- 폭 설정 상태: `src/stores/layout.ts`
- 공통 페이지 헤더: `src/shared/ui/PageHeader.vue`
- 공통 섹션 헤더: `src/shared/ui/SectionHeader.vue`

### 적용이 완료된 축
- 일반 사용자 페이지 다수는 `AppShell + PageContainer`를 사용한다.
- `CommunityPage.vue`, `SearchPage.vue`, `BoardSubscribePage.vue`, `ArticleBookmarkPage.vue`, `HistoryPage.vue`, `MyPage.vue`, `SettingsPage.vue`는 `PageHeader` 기반 구조를 사용한다.
- `BoardPage.vue`는 공통 셸 안에서 `BoardHeaderCard`를 도메인 헤더로 사용한다.
- 관리자 페이지 다수도 공통 셸과 폭 프리셋을 사용한다.

### 아직 남아 있는 차이
- `MainPage.vue`는 의도적으로 섹션 중심 화면이라 `PageHeader` 없이 시작한다.
- 일부 화면은 `ui-panel`, `ui-sub-panel` 대신 개별 Tailwind 카드 스타일을 여전히 섞어 쓴다.
- 동일한 성격의 CTA라도 강조색과 우선순위가 화면별로 조금씩 다르다.
- 빈 상태, 로딩 상태, 에러 상태는 공통 클래스가 있으나 배치와 문구 톤은 완전히 통일되지 않았다.

## 핵심 규칙

### 1. 페이지 루트 구조
- 일반 페이지는 기본적으로 `AppShell + PageContainer`를 사용한다.
- `PageContainer width="auto"`는 전역 레이아웃 설정을 따른다.
- 입력 집중형 화면은 `narrow`, 관리자/테이블 중심 화면은 `wide`, 특수 화면만 `full`을 예외로 사용한다.
- 도메인 컨텍스트가 강한 상세 화면은 `PageHeader` 대신 `BoardHeaderCard` 같은 도메인 헤더를 써도 된다.

### 2. 페이지 최상단 블록
- 최상단 블록은 아래 셋 중 하나로 정리한다.
  - `PageHeader`
  - `PageHeader + 보조 요약 패널`
  - 도메인 헤더 1개
- 서로 성격이 다른 hero 성격 헤더를 한 페이지에 2개 이상 두지 않는다.
- `PageHeader`의 `meta`, `actions`, 기본 슬롯을 활용해 보조 정보와 필터, 탭, 액션을 흡수한다.
- 이미 `SearchPage.vue`, `MyPage.vue`는 이 패턴을 사용하고 있다.

### 3. 섹션 흐름과 간격
- 페이지 루트 간격은 `space-y-6` 또는 `space-y-8`을 기본으로 한다.
- 섹션 내부 간격은 `space-y-3`~`space-y-5` 범위를 기본으로 한다.
- 섹션 제목은 가능하면 `SectionHeader`로 통일한다.
- 같은 페이지 안에서 `mt-*`로 섹션 간격을 개별 보정하는 패턴은 줄인다.

### 4. 패널 사용 기준
- 주요 블록: `ui-panel`
- 보조 카드, 리스트 아이템, 필터/폼 묶음: `ui-sub-panel`
- 동일한 역할이면 직접 `rounded-* border bg-* shadow-*` 조합을 새로 만들지 않는다.
- 커스텀 배경이 필요해도 `ui-panel`, `ui-sub-panel` 위에 추가 클래스를 얹는 방향을 우선한다.

### 5. 상태 노출 기준
- 에러: `ui-state ui-state-danger`
- 빈 상태: `ui-state ui-state-empty`
- 로딩: 저강도 안내 문구 또는 스켈레톤으로 통일한다.
- 섹션 단위 실패는 가능하면 페이지 전체 실패와 분리해서 보여준다.

### 6. 버튼 위계 기준
- 1순위 CTA: 진행성 액션
  - 예: 검색, 저장, 생성, 글쓰기
- 2순위 보조 액션: 이동, 필터 전환, 닫기
- 위험 액션: 삭제, 탈퇴 같은 파괴적 동작
- 동일 역할 버튼은 페이지마다 강조색을 바꾸지 않는다.

## 페이지 유형별 기준

### 탐색형 페이지
- 대상
  - 홈
  - 커뮤니티
  - 검색
  - 구독 목록
  - 북마크
- 구조
  - `PageHeader` 또는 섹션 중심 시작
  - 필터/정렬 블록
  - `SectionHeader + 리스트/카드`
- 메모
  - `MainPage.vue`는 현재 예외적으로 헤더 없이 섹션부터 시작한다.
  - `CommunityPage.vue`, `SearchPage.vue`는 이미 `PageHeader` 중심 구조다.

### 상세형 페이지
- 대상
  - 게시판 상세
  - 게시글 상세
- 구조
  - 도메인 헤더 1개
  - 본문 패널
  - 보조 정보 섹션
  - 관련 콘텐츠 섹션
- 메모
  - 도메인 헤더가 있으면 별도 대형 hero를 추가하지 않는다.

### 작성형 페이지
- 대상
  - 게시글 작성/수정
  - 게시판 생성
  - 각종 설정 입력 폼
- 구조
  - `PageHeader`
  - 주 패널 1개 또는 소수의 패널에 폼 집중
- 메모
  - 입력 흐름이 우선이며 필요할 때만 `narrow`를 사용한다.

### 개인화 페이지
- 대상
  - 마이페이지
  - 설정
  - 기록
- 구조
  - `PageHeader`
  - 탭/보조 액션
  - 상태 패널 + 리스트/폼 패널
- 메모
  - `MyPage.vue`는 탭 버튼을 `PageHeader.actions`에 넣어 관리하고 있다.

### 관리형 페이지
- 대상
  - 시스템 관리자
  - 게시판 관리자
- 구조
  - `PageHeader`
  - 필터/요약 바
  - 테이블 또는 작업 패널
- 메모
  - 기본 폭은 `wide`를 우선한다.

## 현재 화면별 점검 포인트

### 홈
- 현재
  - `AppShell + PageContainer` 위에 섹션만 배치한다.
- 정리 기준
  - 섹션 간격과 `SectionHeader` 톤을 우선 통일한다.
  - 페이지 정체성 보강이 필요할 때만 가벼운 `PageHeader`를 검토한다.

### 커뮤니티
- 현재
  - `PageHeader + meta badge + 게시판 카드 그리드` 구조다.
- 정리 기준
  - 별도 소개 블록을 추가하지 않고 현재 단일 헤더 구조를 유지한다.

### 검색
- 현재
  - `PageHeader` 안에 검색 폼, 범위, 정렬, 표시 개수가 들어간다.
- 정리 기준
  - 결과 섹션은 `SectionHeader`와 상태 블록 기준을 유지한다.

### 게시판 상세
- 현재
  - 공통 셸 적용은 끝났고 `BoardHeaderCard`가 유일한 상단 헤더다.
- 정리 기준
  - 목록, 오류, 빈 상태 패널의 톤만 다른 탐색형 페이지와 더 맞춘다.

### 마이페이지
- 현재
  - `PageHeader` 안에 상단 탭 액션이 들어간다.
- 정리 기준
  - 프로필 카드, 활동 리스트, 입력 패널에서 `ui-panel` 계열 톤을 계속 유지한다.

## 운영 원칙
- 한 페이지 안에서는 패널 종류를 2단계 이상 과도하게 섞지 않는다.
- 도메인 헤더가 있는 페이지는 별도 대형 hero를 추가하지 않는다.
- 제목 크기와 설명 밀도는 페이지 유형 안에서 일관되게 유지한다.
- 여백 차이만으로 화면 성격을 만들지 않는다.
- 새 라우트 페이지는 특별한 이유가 없으면 `AppShell + PageContainer`에서 시작한다.
