# Markdown 임포트 작업계획서

## 문서 목적
- 목적: `Markdown 임포트 및 Frontmatter 설계안`을 실제 구현으로 옮기기 위한 작업 순서와 범위를 정리한다.
- 기준 시점: 2026-03-15 저장소 코드 기준
- 현재는 핵심 범위가 구현 완료된 상태이며, 이 문서는 구현 순서 기록과 남은 후속 작업을 함께 정리한다.
- 기준 문서
  - `markdown-import-frontmatter-design.md`
  - `markdown-mode-design.md`
  - `markdown-wysiwyg-implementation-plan.md`

## 목표
- Markdown 작성 화면에서 `.md` 단건 임포트를 지원한다.
- 파일 상단 `YAML frontmatter`를 파싱해 제목과 메타를 자동 반영한다.
- 대량 임포트는 `manifest.yml + 여러 .md + zip` 구조를 기준으로 설계하고 구현한다.
- 대량 임포트 기능은 `ADMIN`, `MANAGER`만 사용할 수 있게 제한한다.
- 기존 게시글 저장 구조 `content_source`, `content_format`, `content`는 유지한다.
- 현재 기준으로 단건 임포트, frontmatter 파싱, preview/execute API, 관리자 화면, 상대경로 본문 assets 업로드/치환까지 반영됐다.

## 범위

### 포함
- 게시글 작성/수정 화면의 단건 MD 임포트
- YAML frontmatter 파싱
- 제목/공개범위/게시판 slug/카테고리 자동 반영
- 덮어쓰기 확인 UX
- 대량 임포트 preview/execute API
- `ADMIN`, `MANAGER` 전용 권한 정책
- 대량 임포트 검증 결과 UI와 관리자성 진입 화면
- 상대경로 본문 assets 업로드/치환
- `!youtube[...]` 문법 정규화

### 제외
- HTML 글을 Markdown으로 일괄 변환하는 기능
- `.docx`, `.pdf` 등 외부 포맷 임포트
- 임포트 이력용 별도 테이블 도입
- 비동기 작업 큐/재시도 시스템

## 최종 사용자 경험

### 일반 작성자
- Markdown 모드에서 `.md` 파일을 바로 불러올 수 있다.
- frontmatter가 있으면 제목과 일부 메타가 자동 채워진다.
- 기존 입력 내용이 있으면 덮어쓰기 전 확인을 받는다.

### 관리자/매니저
- 별도 대량 임포트 화면 또는 운영 도구에서 `zip` 파일을 올릴 수 있다.
- 업로드 후 각 문서의 파싱 결과, 오류, 경고를 확인할 수 있다.
- 확인 후 일괄 생성할 수 있다.

## 선행 조건
- `Markdown 기본값 + WYSIWYG 공존` 작성 구조가 유지되어야 한다.
- 게시글 저장 구조 `content_source`, `content_format`, `content`가 이미 반영되어 있어야 한다.
- 대량 임포트는 일반 작성 UX가 아니라 운영 도구라는 방향이 합의되어야 한다.
- 권한 기준이 `ADMIN`, `MANAGER`로 확정되어야 한다.

## 스키마 판단
- 1차 구현에는 `tb_articles` 추가 스키마 변경이 필요 없다.
- 이유:
  - Markdown 원문은 `content_source`
  - 포맷은 `content_format = MARKDOWN`
  - 공개 조회는 `content` HTML
- 2차 확장으로 임포트 이력/비동기 작업이 필요해지면 별도 테이블을 검토한다.

## 단계별 작업 계획

- 아래 `1단계`부터 `9단계`까지는 현재 코드에 반영된 구현 기록이다.
- 남아 있는 후속 작업은 `10단계`의 운영성 강화 항목으로 본다.

### 1단계. 단건 MD 임포트 프론트 유틸
- 작업 내용
  - `.md`, `.markdown` 파일 읽기 유틸 추가
  - UTF-8 BOM 제거
  - frontmatter 분리/본문 추출 유틸 추가
  - 제목 fallback 규칙 적용
- 산출물
  - 파일 파서 유틸
  - frontmatter 파서 유틸
- 완료 기준
  - 샘플 `.md` 파일에서 제목, 메타, 본문이 안정적으로 분리됨

### 2단계. frontmatter 필드 매핑
- 작업 내용
  - `title` -> 게시글 제목
  - `boardSlug` -> 대상 게시판 선택 후보
  - `visibility` -> 공개 범위
  - `categoryName` -> 게시판 카테고리 선택 후보
  - `tags`, `summary` -> UI 자동 반영 없이 `content_source` 원문 보존
- 산출물
  - 프론트 매핑 규칙
- 완료 기준
  - 지원 필드가 폼 상태와 일관되게 연결됨

### 3단계. 작성 화면 단건 임포트 UX 반영
- 작업 내용
  - Markdown 모드 툴바의 `MD 불러오기` 연결
  - 드래그 앤 드롭 동작 연결
  - 기존 본문이 있을 때 덮어쓰기 확인 모달 추가
  - 파싱 실패/미지원 필드 경고 메시지 추가
- 산출물
  - 단건 임포트 UI
- 완료 기준
  - 사용자가 `.md` 파일을 불러오면 제목과 본문이 에디터에 반영됨

### 4단계. 미리보기와 저장 경로 검증
- 작업 내용
  - 임포트된 Markdown이 기존 preview API로 정상 미리보기 되는지 확인
  - 저장 시 `content_source`, `content_format = MARKDOWN`, `content` HTML이 일관되게 반영되는지 확인
- 산출물
  - 단건 임포트 저장 검증
- 완료 기준
  - 임포트 -> 미리보기 -> 저장 -> 수정 재진입 흐름이 모두 정상 동작

### 5단계. 대량 임포트 입력 포맷 확정
- 작업 내용
  - `manifest.yml + 여러 .md + zip` 구조를 실제 구현 기준으로 확정
  - `defaults`, `articles[].file` 필수 여부 확정
  - 필드 우선순위 확정
    - manifest 항목
    - frontmatter
    - manifest defaults
    - 시스템 기본값
- 산출물
  - 대량 임포트 입력 스펙
- 완료 기준
  - 샘플 zip 하나로 preview API 스펙이 설명 가능

### 6단계. 백엔드 preview API
- 작업 내용
  - `POST /api/articles/imports/preview` 추가
  - zip 업로드 처리
  - manifest 파싱
  - 각 `.md` 파일 frontmatter 파싱
  - 검증 결과 반환
- 권한
  - `ADMIN`, `MANAGER`
- 산출물
  - 대량 임포트 preview API
- 완료 기준
  - 업로드 결과로 문서별 성공/오류/경고 목록 반환

### 7단계. 백엔드 execute API
- 작업 내용
  - `POST /api/articles/imports/execute` 추가
  - preview에서 검증된 입력을 바탕으로 게시글 생성
  - 게시판 권한, 공개범위, 파일 누락 검증
  - 실패 항목과 성공 항목 구분 반환
- 권한
  - `ADMIN`, `MANAGER`
- 산출물
  - 대량 임포트 execute API
- 완료 기준
  - zip 하나로 여러 게시글 생성이 가능

### 8단계. 관리자성 진입 화면 또는 운영 도구
- 작업 내용
  - 일반 작성 화면과 대량 임포트 UI 분리
  - `ADMIN`, `MANAGER`만 진입 가능한 화면 추가
  - 업로드, preview 결과표, execute 버튼 연결
- 산출물
  - 대량 임포트 관리 UI
- 완료 기준
  - 운영자가 결과를 검토하고 일괄 생성할 수 있음

### 9단계. 권한 보강
- 작업 내용
  - 프론트에서 `ADMIN`, `MANAGER` 외에는 진입 버튼/메뉴 비노출
  - 백엔드에서 역할 강제 검증
  - 서비스 레벨에서도 한 번 더 방어
- 산출물
  - 권한 제어 일관성
- 완료 기준
  - 일반 사용자는 대량 임포트 API를 호출해도 거부됨

### 10단계. 2차 확장 검토
- 작업 내용
  - 임포트 이력 테이블 필요성 검토
  - 비동기 처리, 재시도, 감사 로그 범위 검토
  - 첨부파일 상대경로 자동 업로드 범위 검토
  - HTML `img` 상대경로 처리 여부 검토
- 산출물
  - 후속 설계 메모
- 완료 기준
  - 1차 출시 이후 확장 방향이 정리됨

## 프론트 작업 목록
- 단건 MD 파일 선택/드래그 앤 드롭
- frontmatter 파서 유틸
- 폼 상태 매핑
- 덮어쓰기 확인 모달
- 파싱 실패/미지원 필드 경고
- 대량 임포트 관리자 화면
- preview/execute API 연동
- 권한 기반 진입 제어

## 백엔드 작업 목록
- frontmatter 파싱 유틸 또는 서비스
- manifest 파싱 유틸 또는 서비스
- 대량 임포트 preview API
- 대량 임포트 execute API
- `ADMIN`, `MANAGER` 권한 검증
- 게시판/visibility/작성 가능 여부 검증
- 생성 결과 요약 응답

## API 정리

### 단건 임포트
- 별도 API 없이 프론트 로컬 파싱으로 시작 가능
- 저장은 기존 게시글 생성/수정 API 재사용

### 대량 임포트
- `POST /api/articles/imports/preview`
- `POST /api/articles/imports/execute`

응답에 포함할 정보:
- 게시글별 파일 경로
- 추출된 제목
- 게시판 slug
- 공개 범위
- 오류 목록
- 경고 목록
- 최종 생성 가능 여부

## 테스트 계획

### 프론트
- frontmatter가 있는 `.md` 파싱
- frontmatter가 없는 `.md` 파싱
- 잘못된 YAML 처리
- 덮어쓰기 확인 모달 동작
- 제목 fallback 동작

### 백엔드
- manifest 정상 파싱
- 누락 파일 감지
- 잘못된 visibility 값 거부
- 권한 없는 사용자 접근 거부
- 여러 문서 중 일부만 실패하는 경우 결과 분리

### 통합 검증
- 단건 임포트 -> 저장 -> 수정 재진입
- 대량 preview -> execute -> 게시글 생성 확인
- `ADMIN`, `MANAGER` 외 사용자 차단 확인

## 리스크
- frontmatter 문법 다양성으로 인한 파싱 예외
- `boardSlug`, `visibility` 값 불일치
- 대량 임포트 UI를 일반 작성 UX와 섞을 경우 복잡도 증가
- 이미지 상대경로 자동 치환 요구가 빠르게 생길 수 있음

## 권장 출시 순서
1. 단건 `.md` 임포트
2. YAML frontmatter 제목/메타 자동 반영
3. 단건 임포트 검증/테스트
4. 대량 임포트 preview API
5. 대량 임포트 execute API
6. 관리자성 UI
7. 2차 확장 검토

## 최종 권장안 요약
- 1차는 단건 MD 임포트에 집중한다.
- 대량 임포트는 일반 작성 기능이 아니라 `ADMIN`, `MANAGER` 전용 운영 기능으로 분리한다.
- `tb_articles` 스키마는 추가 변경 없이 진행한다.
- 임포트 이력, 비동기, 재시도 같은 운영성 강화는 2차로 미룬다.
