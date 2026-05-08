# 마크다운 대량 임포트 고도화 작업계획서

## 문서 목적
- 목적: `마크다운 대량 임포트 고도화 설계안`을 실제 구현으로 옮기기 위한 단계별 작업 순서를 정리한다.
- 기준 시점: 2026-03-15 저장소 코드 기준
- 현재는 핵심 고도화 범위가 구현 완료된 상태이며, 이 문서는 구현 순서 기록과 남은 후속 과제를 함께 정리한다.
- 기준 문서: [마크다운 대량 임포트 고도화 설계안](./markdown-bulk-import-advanced-design.md)

## 현재 기준선
- 단건 `.md` 임포트 동작 중
- `manifest.yml + 여러 .md + zip` 대량 임포트 동작 중
- `카테고리 자동 생성` 지원, 기본값 켜짐
- `content_source`에는 `frontmatter + Markdown 원본` 보존
- `tags`, `summary`는 원본에만 보존, UI 기능 없음
- 본문 첨부파일은 기존 수동 업로드 정책 유지

## 이번 고도화의 목표
- `manifest` 없는 zip도 preview/execute 가능하게 만든다.
- zip 내부 상대경로 이미지/동영상 본문 assets를 자동 업로드하고 본문 링크를 치환한다.
- Markdown `!youtube[...]` 문법을 기존 유튜브 embed HTML로 정규화한다.
- preview/execute 결과에 자동 보정 계획과 실행 결과를 더 자세히 보여준다.
- 추가적인 `tb_articles` 스키마 변경 없이 완성도를 높인다.
- 현재 기준으로 위 핵심 항목은 코드에 반영됐다.

## 비목표
- import job 이력 테이블
- 비동기 큐
- 실패 항목 재시도
- 첨부파일 상대경로 자동 업로드
- `tags`, `summary` UI 기능화
- 일반 `iframe` 허용 확대

## 선행 조건
- 현재 frontmatter 보존 정책이 유지되어야 한다.
- 대량 임포트는 계속 `ADMIN`, `MANAGER` 전용으로 유지한다.
- `상대경로 본문 assets 자동 업로드`는 1차에 이미지와 HTML `video` 상대경로 `src`를 대상으로 한다.
- 유튜브는 `velog`식 `!youtube[...]` 문법만 지원하고, 일반 `iframe`은 허용하지 않는다.
- `!youtube[...]` 해석 실패 시 실행 차단 대신 원문 보존 경고로 처리한다.
- 로컬 이미지/동영상 assets는 파일당 `50MB` 제한을 따른다.
- 첨부파일은 기존 별도 업로드 방식으로 유지한다.

## 단계별 작업 계획

- 아래 `1단계`부터 `6단계`까지는 현재 코드에 반영된 구현 기록이다.
- `7단계`는 회귀 테스트와 운영성 보강 관점의 후속 과제로 유지한다.

### 1단계. 입력 포맷 확장
- 작업 내용
  - `manifest` 없는 zip 자동 스캔 규칙 구현
  - zip 내부 `.md`, `.markdown` 후보 목록 추출
  - `manifest`가 있으면 현재 로직 우선, 없으면 자동 스캔 로직 사용
- 백엔드 작업
  - `ArticleImportBundleParser` 확장
  - markdown 후보 정렬/필터 규칙 추가
- 완료 기준
  - `manifest` 없는 zip도 preview 결과를 반환한다.

### 2단계. 상대경로 본문 assets 분석
- 작업 내용
  - Markdown 이미지와 HTML `video` 태그에서 상대경로 본문 assets 참조 추출
  - Markdown `!youtube[...]` 문법 추출 및 video id 해석 규칙 추가
  - 현재 Markdown 파일 기준 상대경로 정규화 후 zip 내부 파일 존재 여부 검증
  - 이미지/동영상 파일 타입과 경로 정상화 처리
  - 파일당 `50MB` 초과 여부 검증
- 백엔드 작업
  - Markdown 이미지 링크 파서 유틸 추가
  - HTML `video` 상대경로 파서 유틸 추가
  - 유튜브 커스텀 문법 파서 유틸 추가
  - zip 내부 파일 조회 구조 추가
- 완료 기준
  - preview 결과에 업로드 예정 이미지/동영상 수, 유튜브 임베드 수, 누락 assets 수가 표시된다.

### 3단계. preview 결과 상세화
- 작업 내용
  - preview 항목 DTO 확장
  - 자동 보정 정보 표시
  - 본문 assets 업로드 계획 표시
  - 유튜브 임베드 정규화 계획 표시
  - `실행 가능`, `자동 보정 후 실행 가능`, `실행 불가` 표현 보강
- 백엔드 작업
  - preview 응답 필드 확장
- 프론트 작업
  - 관리자 화면 preview 표 보강
- 완료 기준
  - 운영자가 실행 전에 자동 생성/자동 업로드 계획을 확인할 수 있다.

### 4단계. execute 이미지/동영상 업로드와 링크 치환
- 작업 내용
  - 상대경로 이미지/동영상 파일 업로드
  - `!youtube[...]` 문법을 기존 유튜브 embed HTML로 정규화
  - Markdown 이미지 링크와 HTML `video` 경로를 실제 파일 URL로 치환
  - 치환된 Markdown을 `content_source`로 저장
- 백엔드 작업
  - 파일 업로드 서비스와 임포트 실행 흐름 연결
  - 문서 단위 링크 치환 유틸 추가
- 완료 기준
  - zip 내부 이미지/동영상을 포함한 Markdown 글이 저장 후 상세/수정에서 깨지지 않는다.

### 5단계. frontmatter 재조립과 저장 경로 정리
- 작업 내용
  - `title`, `boardSlug`, `visibility`, `categoryName`를 최종 적용값 기준으로 frontmatter에 재조립
  - 본문 assets 링크 치환 후의 Markdown을 저장 최종본으로 사용
- 백엔드 작업
  - execute 경로에서 frontmatter 재조립 보정
- 완료 기준
  - 대량 임포트로 저장된 Markdown 글도 단건 작성 글과 같은 구조를 가진다.

### 6단계. 관리자 화면 UX 보강
- 작업 내용
  - `manifest 없이 전체 스캔` 옵션 노출 여부 결정
  - `본문 assets 자동 업로드` 옵션 추가 여부 결정
  - preview/execute 결과 카드 상세화
- 프론트 작업
  - [AdminArticleImportsPage.vue](../../mocktalkfront/src/pages/AdminArticleImportsPage.vue) 보강
- 완료 기준
  - 운영자가 옵션과 결과를 이해하기 쉽게 사용할 수 있다.

### 7단계. 테스트 보강
- 백엔드 테스트
  - manifest 있음/없음 preview
  - 상대경로 이미지 정상 매핑
  - `./assets`, `../assets` 상대경로 정규화
  - 누락 이미지 오류
  - 유튜브 문법 정상 정규화
  - 유튜브 문법 해석 실패 시 원문 보존 경고
  - 카테고리 자동 생성 + 이미지 업로드 조합
  - frontmatter 보존/strip 회귀
- 프론트 테스트
  - 옵션 전달
  - 결과 표 렌더
  - 안내 문구/상태 배지
- 완료 기준
  - 고도화된 preview/execute 핵심 흐름이 테스트로 고정된다.

## 프론트 작업 목록
- 대량 임포트 옵션 UI 확장
- preview 표/execute 결과 카드 상세화
- 자동 보정/본문 assets 업로드 상태 뱃지
- 유튜브 임베드 정규화 상태 표시
- 안내 문구와 샘플 zip 구조 보강

## 백엔드 작업 목록
- manifest 없는 zip 자동 스캔
- 상대경로 본문 assets 분석 유틸
- 유튜브 커스텀 문법 파서/정규화 유틸
- 이미지/동영상 업로드 및 링크 치환
- preview DTO 확장
- execute 결과 DTO 확장
- frontmatter 재조립/저장 보정

## 검증 계획

### 프론트
- `npm run lint`
- `npm run test`
- `npm run build`

### 백엔드
- `ArticleImportBundleParserTest`
- `ArticleImportServiceTest`
- 필요 시 파일 업로드 관련 서비스 테스트 추가

### 수동 QA
- manifest 있음 + 이미지 없음
- manifest 없음 + 이미지 없음
- manifest 있음 + 상대경로 이미지 있음
- manifest 있음 + 상대경로 동영상 있음
- manifest 있음 + `!youtube[...]` 포함
- `!youtube[...]` 해석 실패 시 경고 확인
- 이미지/동영상 누락
- `50MB` 초과 파일 포함
- 카테고리 자동 생성 켜짐/꺼짐

## 리스크
- zip 내부 경로 처리 실수로 잘못된 파일을 참조할 수 있음
- 이미지/동영상 업로드 실패 시 문서 단위 오류 처리 정책이 복잡해질 수 있음
- 유튜브 URL/ID 해석 규칙이 느슨하면 잘못된 embed가 저장될 수 있음
- 치환된 Markdown 저장 정책을 명확히 하지 않으면 수정 화면에서 혼란이 생길 수 있음
- 프리뷰와 실행 결과의 정보량이 많아지면 관리자 화면이 복잡해질 수 있음

## 출시 순서 권장
1. manifest 없는 zip 자동 스캔
2. preview 결과 상세화
3. 상대경로 본문 assets 업로드/치환
4. execute 결과 상세화
5. 관리자 화면 옵션/가이드 정리

## 2차로 미루는 항목
- `tb_article_import_jobs`
- `tb_article_import_job_items`
- 비동기 큐
- 실패 항목 재시도
- 감사 로그 상세화
- zip 원본 장기 보관

## 최종 권장안 요약
- 이번 고도화는 `운영자가 덜 귀찮게 올리고, 실행 전에 더 정확히 판단하게 만드는 것`에 집중한다.
- 핵심은 `manifest 없는 zip 자동 스캔`과 `상대경로 본문 assets 자동 업로드/치환`이다.
- 유튜브는 `velog`식 Markdown 문법을 기존 embed HTML로 정규화하는 방식으로 처리한다.
- `job 이력`, `재시도`, `감사 추적`은 2차로 미룬다.
