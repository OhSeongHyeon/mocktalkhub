# Markdown + WYSIWYG 작성 UX 작업계획서

## 문서 목적
- 목적: `Markdown 기본값 + WYSIWYG 공존` 방향의 게시글 작성/수정 UX를 실제 구현하기 위한 작업 순서와 범위를 정리한다.
- 기준 시점: 2026-03-15 저장소 코드 기준
- 현재는 핵심 흐름이 구현 완료된 상태이며, 이 문서는 구현 순서 기록과 남은 개선 과제를 함께 정리한다.
- 기준 문서
  - `markdown-mode-design.md`
  - `mocktalkback/src/main/resources/db/migration/V13__article_content_source_and_format.sql`

## 목표
- 신규 작성 기본값을 `Markdown`으로 전환한다.
- 사용자는 같은 작성 화면에서 `WYSIWYG`로 즉시 전환할 수 있다.
- 수정 화면은 `content_format` 기준으로 같은 경험을 복원한다.
- 공개 조회는 기존처럼 `content` HTML 렌더링을 유지한다.
- Markdown 작성 흐름에 `미리보기`, `MD 파일 임포트`를 포함한다.

## 범위

### 포함
- 게시글 작성 페이지
- 게시글 수정 페이지
- 게시글 저장 구조
- 게시글 수정 로드 구조
- 미리보기 API
- MD 파일 임포트 UX
- 모드 전환 경고 UX

### 제외
- 댓글 Markdown 지원
- 검색 인덱스 최적화 재설계
- 게시글 상세 페이지의 전체 타이포그래피 리디자인
- Markdown 외 외부 포맷(docx 등) 임포트

## 최종 사용자 경험
- 신규 작성 기본값은 `Markdown`
- 사용자는 `Markdown`과 `WYSIWYG` 사이를 전환 가능
- Markdown에서는 미리보기 사용 가능
- WYSIWYG에서는 기존 리치 편집 흐름 유지
- 수정 시 저장된 `content_format`에 맞는 탭으로 진입
- `MD 불러오기`로 초안 작성 시간을 줄인다

## 선행 조건
- 설계 방향 확정
- `tb_articles.content_source`, `tb_articles.content_format` 도입 합의
- 프론트에서 `Markdown`, `WYSIWYG`, `미리보기` 탭 공존 합의
- 공개 조회는 `content` HTML만 사용한다는 원칙 확정

## 단계별 작업 계획

- 아래 `1단계`부터 `9단계`까지는 현재 코드에 반영된 구현 기록이다.
- `10단계`는 테스트와 품질 게이트 기준을 정리하는 후속 검증 항목으로 유지한다.

### 1단계. DB/Flyway 확정
- 작업 내용
  - `tb_articles`에 `content_source`, `content_format` 컬럼 추가안 확정
  - 기존 `content` -> `content_source` HTML 백필 여부 확정
  - `content_format` 기본값과 체크 제약 확정
- 산출물
  - 실제 적용 가능한 Flyway SQL
- 완료 기준
  - 컬럼명, 기본값, 백필 정책이 문서로 확정됨

### 2단계. 백엔드 도메인/엔티티/DTO 반영
- 작업 내용
  - `ArticleEntity`에 `contentSource`, `contentFormat` 반영
  - 생성/수정 요청 DTO 변경
  - 수정 조회용 응답에 `contentSource`, `contentFormat` 포함
  - 공개 조회 응답은 기존 `content` 중심 유지
- 산출물
  - 엔티티/DTO/매퍼 수정
- 완료 기준
  - 생성/수정/수정조회 API 계약이 변경안과 일치

### 3단계. 백엔드 렌더링/미리보기 파이프라인 추가
- 작업 내용
  - `MARKDOWN -> HTML` 렌더링 경로 추가
  - `HTML -> HTML sanitize` 경로 유지
  - `POST /api/articles/preview` 구현
  - preview 응답은 `content` HTML 반환
- 산출물
  - 미리보기 API
  - Markdown 렌더 서비스
- 완료 기준
  - 같은 입력에 대해 preview 결과와 저장 후 content가 구조적으로 일치

### 4단계. 프론트 작성 화면 탭 구조 변경
- 작업 내용
  - 작성 화면 상단 모드를 `Markdown | WYSIWYG` 구조로 정리
  - Markdown 안에서 `작성 | 분할 | 미리보기` 제공
  - WYSIWYG 안에서는 기존 `에디터 | HTML` 전환 유지
  - 신규 작성 기본 탭을 `Markdown`으로 변경
  - 수정 진입 시 `content_format` 기준 탭 선택
- 산출물
  - 작성/수정 페이지 공통 탭 UI
- 완료 기준
  - 생성/수정 모두 동일한 탭 구조 사용

### 5단계. Markdown 편집 영역 도입
- 작업 내용
  - Markdown 텍스트 입력 영역 추가
  - 미리보기 패널 또는 미리보기 탭 연결
  - 입력 디바운스 후 preview API 호출
  - 에러/로딩 상태 처리
- 산출물
  - Markdown 편집기 + 미리보기 UI
- 완료 기준
  - Markdown 입력 시 미리보기가 정상 갱신됨

### 6단계. WYSIWYG 공존 구조 정리
- 작업 내용
  - 기존 `tiptap` WYSIWYG 편집기는 그대로 유지
  - 저장 시 `content_format = HTML`로 처리
  - 수정 시 HTML 글은 WYSIWYG 탭으로 진입
- 산출물
  - Markdown/WYSIWYG 공존 화면
- 완료 기준
  - Markdown 작성과 WYSIWYG 작성이 같은 저장 화면 안에서 모두 가능

### 7단계. 모드 전환 경고 UX 추가
- 작업 내용
  - `WYSIWYG -> Markdown` 전환 시 손실 위험 검사
  - 위험 요소가 있으면 경고 모달 노출
  - `변환 후 계속 / 취소` 처리
- 산출물
  - 전환 경고 모달
- 완료 기준
  - 손실 가능 요소가 있을 때만 경고가 뜬다

### 8단계. MD 파일 임포트 추가
- 작업 내용
  - `.md`, `.markdown` 파일 선택 지원
  - 본문 덮어쓰기 확인 모달
  - UTF-8 BOM 처리
  - 임포트 후 Markdown 편집기 반영 및 미리보기 갱신
- 산출물
  - `MD 불러오기` 버튼과 연결 로직
- 완료 기준
  - 로컬 md 파일로 초안 주입 가능

### 9단계. 수정 화면 복원 흐름 정리
- 작업 내용
  - `content_format = MARKDOWN` 글은 Markdown 원본 로드
  - `content_format = HTML` 글은 WYSIWYG용 HTML 원본 로드
  - 저장 후 재진입 시 같은 포맷으로 다시 열리는지 확인
- 산출물
  - 작성/수정 일관성 보장
- 완료 기준
  - 사용자가 작성하던 방식 그대로 수정할 수 있음

### 10단계. 테스트/검증
- 작업 내용
  - 백엔드
    - Markdown 저장 시 HTML 렌더 검증
    - preview API 검증
    - content/content_source/content_format 저장 검증
  - 프론트
    - 신규 작성 기본 Markdown 탭 검증
    - 수정 진입 포맷 복원 검증
    - MD 임포트 검증
    - 전환 경고 모달 검증
- 완료 기준
  - `lint`, `test`, `build` 통과
  - 필요 시 백엔드 테스트 통과

## 변경 예상 파일군

### 백엔드
- `mocktalkback/src/main/resources/db/migration/*`
- `mocktalkback/src/main/java/com/mocktalkback/domain/article/entity/*`
- `mocktalkback/src/main/java/com/mocktalkback/domain/article/controller/*`
- `mocktalkback/src/main/java/com/mocktalkback/domain/article/service/*`
- `mocktalkback/src/main/java/com/mocktalkback/domain/article/mapper/*`

### 프론트
- `mocktalkfront/src/features/editor/ui/*`
- `mocktalkfront/src/widgets/article/*`
- `mocktalkfront/src/pages/*`
- `mocktalkfront/src/shared/lib/*`
- `mocktalkfront/src/entities/article/*`

## 주요 리스크
- `WYSIWYG -> Markdown` 변환에서 일부 리치 속성이 손실될 수 있음
- preview API와 저장 결과가 완전히 같지 않으면 UX 신뢰가 깨질 수 있음
- 수정 화면에서 포맷 복원이 어긋나면 사용자가 혼란을 느낄 수 있음
- Markdown 임포트와 기존 이미지 드롭 UX가 충돌할 수 있음

## 리스크 대응
- 손실 위험 요소는 전환 전에 경고
- preview는 프론트 자체 렌더보다 서버 기준 렌더 우선
- 수정 진입은 반드시 `content_format` 기준
- MD 임포트는 명시적 버튼부터 시작하고 드래그 앤 드롭은 후순위

## 작업 순서 권장
1. Flyway/엔티티/DTO 확정
2. preview API 추가
3. 작성/수정 탭 UI 변경
4. Markdown 편집기 연결
5. WYSIWYG 공존 정리
6. 전환 경고
7. MD 임포트
8. 테스트 및 정리

## 승인 게이트
- 구현 당시에는 아래 순서로 나눠 승인받아 진행하는 구조가 안전했다.
  - 1차: DB/Flyway + 백엔드 계약
  - 2차: 프론트 탭 구조 + Markdown 미리보기
  - 3차: 전환 경고 + MD 임포트 + 마무리 검증

## 한 줄 정리
- 이번 작업은 `Markdown만 추가`가 아니라 `Markdown을 기본값으로 올리되 WYSIWYG를 동등하게 공존시키고, 작성/수정의 일관성을 보장하는 재설계`다.
