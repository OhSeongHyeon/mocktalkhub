# Markdown 임포트 및 Frontmatter 설계안

## 문서 목적
- 목적: 게시글 작성 화면의 `Markdown 파일 임포트`, `YAML frontmatter`, `대량 임포트`를 현재 구현 기준으로 정리하고 남은 확장 포인트를 명확히 한다.
- 전제: 작성/수정 UX는 `Markdown 기본값 + WYSIWYG 동등 지원` 구조를 목표로 한다.
- 방향: 단건 `.md` 임포트와 frontmatter 자동 반영은 일반 작성 UX로 유지하고, 대량 임포트는 관리자 운영 도구로 분리한다.

## 관련 문서
- [Tiptap 작성 UX 재설계안](./markdown-mode-design.md)
- [Markdown/WYSIWYG 구현 작업계획서](./markdown-wysiwyg-implementation-plan.md)

## 핵심 결론
- 단건 임포트는 `.md` 파일 하나를 불러오고, 파일 상단 `YAML frontmatter`를 읽어 글 제목과 메타를 자동 채우는 방향이 가장 자연스럽다.
- 대량 임포트는 `manifest.yml + 여러 .md + zip` 구조를 기본으로 하되, 현재 구현은 `manifest` 없는 zip 자동 스캔도 지원한다.
- 본문 원본은 계속 `content_source`, 원본 포맷은 `content_format = MARKDOWN`으로 저장한다.
- 대량 임포트 기능은 `ADMIN`, `MANAGER`만 사용할 수 있게 제한하는 것이 맞다.
- frontmatter는 작성 편의를 위한 메타 입력 수단이지, 공개 조회용 HTML 렌더 구조를 바꾸는 기능은 아니다.
- 단건 임포트에서 실제 자동 반영 대상은 `title`, `visibility`, `boardSlug`, `categoryName`이고, `tags`, `summary`는 원문 보존만 한다.
- 대량 임포트는 현재 상대경로 이미지/동영상 assets 자동 업로드와 `!youtube[...]` 정규화까지 포함한다.
- 이 요구사항만으로 `tb_articles` 스키마를 추가 변경할 필요는 없다.

## 왜 YML 단독보다 MD + Frontmatter가 좋은가
- Markdown 글은 본문과 메타가 같이 있어야 이식성과 재사용성이 좋다.
- 사용자는 블로그 글을 보통 `.md` 단위로 관리한다.
- `YML` 단독으로 본문까지 관리하면 길고 읽기 어렵다.
- frontmatter는 이미 널리 쓰이는 패턴이라 사용자 학습 비용이 낮다.

## 현재 구현 기준

### 단건 임포트
- `.md`, `.markdown` 파일을 Markdown 작성 화면에서 불러온다.
- frontmatter가 있으면 `title`, `visibility`, `categoryName`을 반영한다.
- 생성 화면에서는 `boardSlug`가 현재 게시판과 다르면 해당 게시판으로 이동한 뒤 메타를 반영한다.
- 수정 화면에서는 `boardSlug`가 현재 게시판과 다르면 경고만 보여주고 적용하지 않는다.
- `tags`, `summary`, 미지원 frontmatter 키는 경고 메시지를 보여주고 `content_source` 원문에 보존한다.

### 대량 임포트
- `manifest.yml + 여러 .md + zip` 구조를 지원한다.
- `manifest.yml`이 없어도 zip 안의 Markdown 파일을 자동 스캔한다.
- `preview -> execute` 운영 화면과 백엔드 API가 분리되어 있다.
- Markdown 이미지와 HTML `video/source` 상대경로 assets는 실행 시 업로드 후 `/api/files/{id}/view` URL로 치환한다.
- `!youtube[...]` 문법은 저장 전 기존 유튜브 embed HTML로 정규화한다.

### 후속 후보
- 임포트 job 이력과 재시도
- 비동기 실행과 감사 로그
- 첨부파일 상대경로 자동 업로드
- HTML `img` 상대경로 자동 처리

## 단건 임포트 설계

### 사용자 흐름
1. 작성자가 `Markdown 파일 불러오기` 버튼 클릭
2. `.md`, `.markdown` 파일 선택
3. 프론트가 파일 내용을 읽고 frontmatter 파싱
4. 제목, 공개범위, 카테고리 같은 메타를 폼에 자동 반영
5. 본문은 `content_source` 후보로 에디터에 주입
6. 기존 작성 중이던 내용이 있으면 덮어쓰기 확인 모달 표시

### 허용 파일
- `.md`
- `.markdown`

### frontmatter 예시

```md
---
title: "Mermaid 렌더링 최적화 기록"
tags:
  - markdown
  - mermaid
boardSlug: dev
visibility: PUBLIC
summary: "Mermaid 런타임 최적화 과정 정리"
---

# 본문 시작

여기부터 Markdown 본문입니다.
```

### 현재 자동 반영 필드
- `title`: 게시글 제목
- `boardSlug`: 기본 대상 게시판
- `visibility`: 공개 범위
- `categoryName`: 게시판 카테고리 이름

### 현재 원문 보존만 하는 필드
- `tags`
- `summary`
- 미지원 사용자 정의 필드

### 현재 비지원 또는 후순위 필드
- `thumbnail`
- `series`
- `publishedAt`
- `author`
- `coverImage`

## frontmatter 파싱 정책

### 파싱 대상
- 문서 최상단의 `---` 블록만 frontmatter로 인정한다.
- 중간 본문에 등장하는 `---`는 구분선으로 처리한다.

### 인코딩
- UTF-8
- UTF-8 BOM 허용

### 오류 처리
- frontmatter 형식이 깨졌으면 본문 전체를 Markdown으로 취급한다.
- 단, 사용자가 원하면 "frontmatter 파싱 실패" 경고를 띄운다.
- 제목이 없으면 파일명에서 제목 후보를 생성한다.

### 제목 기본값 규칙
- frontmatter `title`이 있으면 그것을 우선 사용한다.
- 없으면 파일명에서 확장자를 제거한 값을 제목 후보로 사용한다.
- 둘 다 부적절하면 제목 입력란 비워둔다.

## 단건 임포트 UI/UX 제안

### 진입 위치
- Markdown 모드 상단 툴바의 `MD 불러오기`
- 현재 구현은 명시적 파일 선택 버튼 기준이다.

### 임포트 후 동작
- 제목 자동 반영
- 본문 자동 반영
- `content_format = MARKDOWN`
- 미리보기 자동 갱신

### 경고/확인 UI
- 기존 본문이 비어 있지 않으면 덮어쓰기 확인 모달
- frontmatter 파싱에 실패해도 파일 불러오기는 계속 허용
- 미지원 필드가 있으면 작은 안내 메시지로 무시 사실만 알려준다

## 대량 임포트 설계

### 권장 구조
- `manifest.yml`
- 여러 개의 `.md` 파일
- 필요 시 이미지/첨부 파일

### 권장 업로드 포맷
- `zip` 파일 하나 업로드

권장 이유:
- 브라우저 파일 선택 UX가 단순하다.
- 파일 개수가 많아도 한 번에 다룰 수 있다.
- 향후 이미지 첨부 자동 매핑까지 확장하기 쉽다.

## 대량 임포트 파일 구조 예시

```text
batch-import.zip
├─ manifest.yml
├─ posts/
│  ├─ post-1.md
│  ├─ post-2.md
│  └─ post-3.md
└─ assets/
   ├─ diagram-1.png
   └─ banner.png
```

### manifest 예시

```yaml
version: 1
defaults:
  boardSlug: dev
  visibility: DRAFT

articles:
  - file: posts/post-1.md
    boardSlug: dev
    visibility: PUBLIC
  - file: posts/post-2.md
  - file: posts/post-3.md
    title: "manifest에서 제목 덮어쓰기"
```

## manifest 정책

### defaults
- 공통 기본값
- 개별 항목에 값이 없을 때만 사용

### articles
- 각 게시글 소스와 메타를 나열
- `file`은 zip 내부 상대 경로

### 우선순위
1. manifest 항목 값
2. Markdown frontmatter 값
3. manifest defaults 값
4. 시스템 기본값

이 우선순위를 두는 이유:
- 대량 임포트에서는 운영자가 manifest에서 한 번에 덮어쓰는 요구가 자주 생긴다.
- 동시에 개별 `.md` 파일은 독립 문서로도 재사용 가능해야 한다.

## 대량 임포트 UX 제안

### 1차 UX
- 작성 화면 안에서 바로 대량 임포트를 넣기보다
- 별도 `대량 임포트` 화면 또는 관리자성 유틸 화면으로 분리하는 것이 맞다
- 이 화면은 `ADMIN`, `MANAGER`만 접근 가능하게 제한한다

이유:
- 일반 작성 UX가 복잡해진다.
- 실패 항목, 검증 결과, 중복 제목, 게시판 권한 문제 같은 예외를 다뤄야 한다.

### 화면 흐름
1. `zip` 업로드
2. 압축 내용 분석
3. manifest 및 각 `.md` 파싱
4. 미리보기 목록 표시
5. 오류/경고 표시
6. 사용자가 확인 후 일괄 생성 실행
7. 성공/실패 결과 리포트 표시

### 미리보기 목록 항목
- 제목
- 대상 게시판
- 공개 범위
- 파일 경로
- 파싱 상태
- 경고 여부

## 프론트 처리 흐름

### 단건 임포트
1. `FileReader` 또는 브라우저 파일 API로 파일 내용 읽기
2. BOM 제거
3. frontmatter 파싱
4. 제목/메타/본문 분리
5. 폼 상태 반영
6. preview API 재호출

### 대량 임포트
1. `zip` 파일 업로드
2. 프론트에서 파일 목록만 선분석하거나, 바로 백엔드 분석 API에 업로드
3. 결과를 임포트 검토 표로 렌더
4. 최종 승인 시 생성 API 호출

주의:
- 대량 임포트는 브라우저 단독 처리보다 백엔드 검증 중심이 더 안전하다.

## 백엔드 API 제안

### 단건 임포트는 API 없이도 가능
- 프론트에서 파일 내용을 읽어 에디터에 넣는 구조면 별도 API가 없어도 된다.
- 저장 시에는 기존 게시글 저장 API를 그대로 사용하면 된다.

### 대량 임포트용 API
- `POST /api/articles/imports/preview`
  - zip 업로드
  - 파싱 결과와 검증 결과 반환
  - 권한: `ADMIN`, `MANAGER`
  - 파라미터: `autoCreateMissingCategories`

- `POST /api/articles/imports/execute`
  - zip 기준 실제 게시글 생성
  - 권한: `ADMIN`, `MANAGER`
  - 파라미터: `autoCreateMissingCategories`

### 응답에 포함할 정보
- 성공 가능 여부
- 게시글별 오류/경고
- 추출된 제목
- 대상 게시판
- 공개 범위
- 최종 본문 포맷

## 권한 정책

### 단건 임포트
- 일반 작성 기능의 일부이므로 기존 게시글 작성 권한 정책을 따른다.
- 즉, 게시판에 글을 쓸 수 있는 사용자는 Markdown 단건 임포트를 사용할 수 있다.

### 대량 임포트
- 사이트 운영 기능으로 보고 `ADMIN`, `MANAGER`만 허용한다.
- 프론트에서는 버튼/메뉴를 숨길 수 있지만, 실제 제한은 백엔드에서 강제해야 한다.
- 권한 체크는 `@PreAuthorize` 또는 서비스 레벨 정책 가드로 처리한다.

## 스키마 변경 필요 여부

### `tb_articles`
- 필수 변경 없음
- 이유:
  - 이미 `content`, `content_source`, `content_format` 구조로 Markdown 원문 저장이 가능하다.
  - 대량 임포트는 입력 경로가 늘어나는 것이지 게시글 저장 구조 자체가 바뀌는 것은 아니다.

### 2차 선택 사항
- 아래 요구가 생기면 별도 테이블을 추가하는 것이 좋다.
  - 임포트 이력 조회
  - 작업 단위 성공/실패 기록
  - 비동기 실행
  - 재시도
  - 운영 감사 로그 강화

예시:
- `tb_article_import_jobs`
- `tb_article_import_job_items`

즉, 권한 요구사항만으로는 `tb_articles` 변경이 필요 없고, 운영 관리가 필요해질 때 별도 임포트 작업 테이블을 추가하는 방향이 맞다.

## 검증 포인트

### 단건 임포트
- 파일 크기 제한
- UTF-8 여부
- frontmatter 파싱 실패
- 제목 누락

### 대량 임포트
- zip 내부 파일 누락
- manifest 문법 오류
- 중복 파일 경로
- 중복 slug 또는 제목 정책 충돌
- 게시판 권한 없음
- 지원하지 않는 공개 범위 값

## 저장 구조와의 연결
- 단건 또는 대량 임포트 모두 최종 저장 구조는 동일하다.
- `content_source`: Markdown 원문
- `content_format`: `MARKDOWN`
- `content`: 백엔드 렌더 후 sanitize된 HTML

즉, 임포트는 입력 경로만 추가되는 것이고 저장 모델 자체를 바꾸는 것은 아니다.

## 이미지와 첨부 처리

### 단건 임포트
- 단건 MD 임포트는 로컬 파일 내용을 에디터에 넣는 역할만 한다.
- 이미지와 동영상은 현재 작성 화면의 기존 업로드 UX를 사용한다.

### 대량 임포트
- Markdown 이미지와 HTML `video/source`의 상대경로는 zip 내부 파일과 매핑한다.
- 실행 시 업로드 후 `/api/files/{id}/view` URL로 치환한다.
- 첨부파일 상대경로 자동 업로드는 아직 지원하지 않는다.

## 구현 순서 기록
1. `.md` 단건 임포트
2. YAML frontmatter 파싱
3. 제목/공개범위/게시판/카테고리 자동 반영
4. frontmatter 오류/덮어쓰기 경고 UX
5. `zip + manifest.yml` 대량 임포트 preview API
6. 대량 생성 execute API
7. 본문 상대경로 assets 자동 업로드/치환

## 비권장안
- `.yml` 파일 하나에 여러 게시글 본문을 모두 집어넣는 구조
- 일반 작성 화면 안에 복잡한 대량 임포트 UI를 바로 섞는 구조
- frontmatter를 저장 시 원문에서 제거하지 않고 본문 HTML까지 그대로 노출시키는 구조
- 대량 임포트를 프론트에서만 전부 처리하는 구조

## 최종 권장안 요약
- 1차는 `.md` 단건 임포트 + YAML frontmatter 자동 반영이다.
- 제목 자동 채우기는 `frontmatter.title` 우선, 없으면 파일명 fallback으로 처리한다.
- 대량 임포트는 `manifest.yml + 여러 .md + zip`을 기본으로 하되, 현재 구현은 `manifest` 없는 zip 자동 스캔도 지원한다.
- 일반 작성 UX와 대량 관리 UX는 분리하는 것이 맞다.
- 저장 구조는 그대로 `content_source/content_format/content`를 사용한다.
