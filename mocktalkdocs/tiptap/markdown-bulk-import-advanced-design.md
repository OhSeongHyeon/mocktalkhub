# 마크다운 대량 임포트 고도화 설계안

## 문서 목적
- 목적: 현재 구현된 `게시글 대량 임포트` 기능을 실제 운영 도구 수준으로 끌어올리기 위한 고도화 방향을 정리한다.
- 기준: 현재 저장 구조는 `content`, `content_source`, `content_format`을 유지하고, 추가적인 `tb_articles` 스키마 변경 없이 진행한다.
- 전제: `frontmatter + Markdown 원본`은 `content_source`에 보존하고, 렌더/미리보기는 frontmatter를 제거한 뒤 처리한다.

## 관련 문서
- [Markdown 임포트 및 Frontmatter 설계안](./markdown-import-frontmatter-design.md)
- [Markdown 임포트 작업계획서](./markdown-import-implementation-plan.md)
- [Markdown 작성 UX 재설계안](./markdown-mode-design.md)

## 현재 상태 요약
- 단건 `.md` 임포트 지원
- `manifest.yml + 여러 .md + zip` 기반 대량 임포트 지원
- `manifest.yml` 없이 zip 안 Markdown 자동 스캔 지원
- `preview -> execute` 운영 화면 지원
- `title`, `boardSlug`, `visibility`, `categoryName` 반영 지원
- `카테고리 자동 생성` 옵션 지원, 기본값은 켜짐
- `frontmatter + Markdown 원본`은 `content_source`에 보존
- `tags`, `summary`, 미지원 frontmatter 필드는 현재 UI 기능화하지 않고 원본에만 보존
- Markdown 이미지와 HTML `video/source` 상대경로 assets 자동 업로드/치환 지원
- Markdown `!youtube[...]` 문법을 기존 유튜브 embed HTML로 정규화한다.

## 현재 남은 고도화 포인트
- import job 이력과 실패 항목 재시도 체계가 없다.
- 비동기 실행/감사 로그 같은 운영성 기능은 아직 없다.
- 첨부파일 상대경로 자동 업로드와 HTML `img` 상대경로 처리는 아직 지원하지 않는다.
- 미리보기/실행 결과는 충분히 상세해졌지만, 운영 히스토리 관점의 추적성은 아직 부족하다.

## 핵심 결론
- 핵심 1차 고도화였던 `manifest 없는 zip 자동 스캔`과 `상대경로 본문 assets 자동 업로드/치환`은 현재 구현에 반영됐다.
- `job 이력`, `감사 추적`, `비동기 실행`, `재시도`는 2차로 미룬다.
- `tags`, `summary`는 지금처럼 `content_source` 원본에만 보존하고 UI 기능으로는 아직 쓰지 않는다.
- `tb_articles` 추가 변경 없이도 운영 편의성은 크게 높일 수 있다.

## 고도화 목표

- 아래 `1차 목표`는 현재 구현 완료된 범위를 요약한 것이다.

### 1차 목표
- `manifest`가 없어도 zip 안의 `.md` 파일을 자동 스캔해 preview 가능
- zip 내부 상대경로 이미지/동영상 assets 자동 업로드/URL 치환
- Markdown `!youtube[...]` 문법을 기존 유튜브 embed HTML로 정규화
- preview 결과에 자동 보정 계획을 더 풍부하게 표시
- execute 결과에 실제 보정/생성 내용을 더 자세하게 표시

### 2차 목표
- import job 이력
- 실패 항목 재실행
- 비동기 실행
- 감사 로그 강화
- 운영자 백오피스 이력 조회

### 비목표
- 지금 단계에서 `tb_articles`에 `summary`, `tags` 컬럼 추가
- `tb_article_import_jobs` 도입
- zip 원본 자체 장기 저장
- HTML 문서를 Markdown으로 일괄 변환

## 고도화 범위

### 포함
- `manifest.yml` 선택적 지원
- zip 내부 Markdown 자동 탐색
- zip 내부 본문 이미지/동영상 파일 자동 업로드
- Markdown/HTML 본문 상대경로 assets 링크 치환
- Markdown 유튜브 커스텀 문법 정규화
- preview/execute 결과 상세화

### 제외
- 첨부파일 상대경로 자동 업로드
- 외부 URL 리소스 다운로드
- 임의 외부 `iframe` 허용
- 대량 임포트 이력 테이블
- 비동기 큐

## 입력 포맷 설계

### A안. manifest 포함 zip
```text
batch-import.zip
├─ manifest.yml
├─ posts/
│  ├─ post-1.md
│  └─ post-2.md
└─ assets/
   ├─ diagram-1.png
   └─ banner.png
```

### B안. manifest 없는 zip
```text
batch-import.zip
├─ post-1.md
├─ post-2.md
├─ docs/
│  └─ guide.md
└─ images/
   └─ guide.png
```

### manifest 없는 zip 자동 스캔 규칙
- zip 안의 `.md`, `.markdown` 파일을 모두 후보로 잡는다.
- `manifest.yml`, `manifest.yaml`은 자동 스캔 대상에서 제외한다.
- 숨김 시스템 파일은 제외한다.
  - 예: `__MACOSX/`, `.DS_Store`
- 기본 정렬은 zip 내부 경로 오름차순으로 고정한다.

### 상대경로 해석 기준
- 상대경로는 현재 Markdown 파일의 zip 내부 경로를 기준으로 정규화한다.
- 정규화 결과가 zip 내부 실제 파일 엔트리와 매핑되면 허용한다.
- `./assets/...`는 항상 허용되는 고정 규칙이 아니라, 현재 Markdown 파일 위치 기준으로 실제 파일이 존재할 때만 정상이다.
- zip 루트 바깥으로 벗어나는 경로는 차단한다.
- 절대경로와 외부 URL은 자동 업로드 대상으로 보지 않는다.

예시:
- `posts/hello.md`에서 `../assets/cover.png`는 정상일 수 있다.
- `posts/hello.md`에서 `./assets/cover.png`는 `posts/assets/cover.png`가 실제로 있을 때만 정상이다.
- `post.md`에서 `./assets/cover.png`는 zip 루트의 `assets/cover.png`가 있으면 정상이다.

## 메타데이터 우선순위
1. manifest 항목 값
2. Markdown frontmatter 값
3. manifest defaults 값
4. 시스템 기본값

지원 대상:
- `title`
- `boardSlug`
- `visibility`
- `categoryName`

보존만 하는 값:
- `tags`
- `summary`
- 미지원 사용자 정의 frontmatter 키

## frontmatter 보존 정책
- `content_source`에는 frontmatter를 포함한 Markdown 원본을 저장한다.
- 저장 시 `title`, `boardSlug`, `visibility`, `categoryName`은 최종 적용값 기준으로 frontmatter를 다시 정리한다.
- `tags`, `summary`, 미지원 키는 삭제하지 않고 원본에 남긴다.
- 렌더와 미리보기는 frontmatter를 제거한 뒤 Markdown 본문만 HTML로 변환한다.

## assets 처리 설계

### 지원 범위
- 1차는 본문 이미지와 본문 동영상 assets를 지원한다.
- 업로드 제한은 파일당 최대 `50MB`로 고정한다.
- 허용 예시:
  - `.png`
  - `.jpg`, `.jpeg`
  - `.gif`
  - `.webp`
  - `.svg`
  - `.mp4`
  - `.webm`
  - `.ogg`

### 범위 구분
- 본문 assets 자동 처리 대상
  - Markdown 이미지 문법
  - HTML `video` 태그의 상대경로 `src`
- 본문 외부 임베드 처리 대상
  - Markdown `!youtube[...]` 문법
- 제외 대상
  - 기존 첨부파일 업로드 기능
  - 외부 URL
  - 일반 `iframe`, `embed` 기반 외부 동영상 임베드

### 상대경로 처리 대상
- Markdown 이미지 문법
  - `![설명](./images/a.png)`
  - `![설명](../assets/banner.jpg)`
- HTML `video` 태그
  - `<video controls src="./videos/demo.mp4"></video>`
  - `<video controls><source src="../assets/demo.webm" type="video/webm" /></video>`
- 유튜브 커스텀 문법
  - `!youtube[dQw4w9WgXcQ]`
  - `!youtube[https://youtu.be/dQw4w9WgXcQ]`
- HTML `img` 태그는 1차에서 제외하거나 경고 처리

### 처리 흐름
1. preview 시 Markdown/HTML 본문에서 상대경로 본문 assets 참조를 분석
2. 현재 Markdown 파일 경로 기준으로 상대경로를 정규화하고 zip 내부 파일 존재 여부 확인
3. execute 시 이미지/동영상 업로드
4. Markdown `!youtube[...]` 문법을 유튜브 embed HTML로 정규화
5. 업로드 후 Markdown 이미지 링크와 HTML `video` 경로를 실제 파일 URL로 치환
6. 치환된 Markdown을 `content_source`로 저장

### 왜 치환된 Markdown을 저장해야 하는가
- zip 내부 상대경로는 저장 후 다시 접근할 수 없다.
- 수정 화면, 미리보기, 상세 화면이 같은 원본을 써야 한다.
- 따라서 실행 후 저장되는 `content_source`는 `업로드 URL로 치환된 Markdown`이어야 한다.

### preview 결과에 표시할 것
- 상대경로 이미지 수
- 상대경로 동영상 수
- 유튜브 임베드 수
- 업로드 예정 이미지 수
- 업로드 예정 동영상 수
- 누락된 assets 수
- 크기 제한 초과 파일 수
- 미지원 파일 수

## preview 고도화 설계

### 현재보다 추가할 정보
- 최종 제목
- 대상 게시판
- 대상 카테고리
- 공개 범위
- 카테고리 자동 생성 예정 여부
- 상대경로 이미지/동영상 업로드 예정 수
- 유튜브 임베드 정규화 수
- 누락 assets 오류
- frontmatter 보존 여부

### 상태 구분
- `실행 가능`
- `자동 보정 후 실행 가능`
- `실행 불가`

### 예시 경고
- `게시판 카테고리가 없어 실행 시 자동 생성합니다: 백엔드`
- `상대경로 이미지 3개, 동영상 1개를 실행 시 업로드합니다.`
- `유튜브 임베드 2개를 velog식 Markdown 문법에서 embed HTML로 정규화합니다.`
- `유튜브 문법을 해석하지 못해 원문을 그대로 보존합니다: !youtube[invalid-url]`
- `frontmatter tags는 원본 content_source에 보존되며 별도 UI에는 아직 반영되지 않습니다.`

### 예시 오류
- `markdown 파일을 찾을 수 없습니다: posts/post-3.md`
- `assets 파일을 찾을 수 없습니다: assets/banner.png`
- `동영상 파일을 찾을 수 없습니다: videos/demo.mp4`
- `파일 크기 제한을 초과했습니다(50MB): videos/intro.mp4`
- `게시판을 찾을 수 없습니다: dev`
- `본문이 비어 있습니다.`

## execute 고도화 설계

### 실행 순서
1. zip 파싱
2. 게시판/권한/visibility 검증
3. 카테고리 자동 생성 필요 여부 확인
4. 상대경로 이미지/동영상 업로드
5. Markdown `!youtube[...]`를 유튜브 embed HTML로 정규화
6. Markdown 이미지 링크와 HTML `video` URL 치환
7. frontmatter 관리 키 재조립
8. 게시글 생성

### 문서 단위 처리 원칙
- 한 문서가 실패해도 다른 문서는 계속 처리한다.
- 실패 원인은 항목별 결과에 남긴다.
- 성공 항목에는 생성된 게시글 ID를 반환한다.

### 동시성/중복 처리
- 카테고리 자동 생성은 유니크 제약 충돌 시 재조회로 흡수한다.
- 이미지/동영상 업로드는 문서 단위로 독립 처리한다.
- 같은 zip 재실행에 대한 중복 게시글 방지는 1차 범위에서 강제하지 않는다.
  - 대신 동일 파일 재실행 가능성을 경고로 남길 수 있다.

## 관리자 UI 설계

### 상단 옵션
- `카테고리 자동 생성` 체크박스
  - 기본값: 켜짐
- 현재는 `manifest 없이 전체 스캔`과 `본문 assets 자동 업로드`가 기본 동작이다.
- 추가 옵션으로 따로 노출하지 않는다.

### preview 표에 추가할 열
- 본문 assets
  - 예: `이미지 3, 동영상 1 / 누락 1`
- 자동 보정
  - 예: `카테고리 생성`

### execute 결과 카드에 추가할 정보
- 생성된 카테고리 여부
- 업로드된 이미지/동영상 수
- 정규화된 유튜브 임베드 수
- 링크 치환 여부

## 현재 API

### preview
- `POST /api/articles/imports/preview`
- multipart:
  - `file`
  - `autoCreateMissingCategories`

### execute
- `POST /api/articles/imports/execute`
- multipart:
  - `file`
  - `autoCreateMissingCategories`

## 권한 정책
- 대량 임포트는 계속 `ADMIN`, `MANAGER` 전용
- 실제 제한은 백엔드에서 강제
- 프론트는 메뉴/화면 노출을 보조적으로만 제어

## 검증 포인트

### 입력
- manifest 있음/없음
- markdown 자동 스캔 순서
- frontmatter 우선순위

### assets
- 상대경로 정상 매핑
- 현재 Markdown 파일 기준 상대경로 정규화
- 이미지/동영상 누락
- 미지원 파일 타입
- 경로 역참조 차단

### 유튜브
- `!youtube[...]` 정상 정규화
- 해석 실패 시 원문 보존 + 경고

### 저장
- `content_source`에 frontmatter 보존
- 렌더 HTML에서 frontmatter 제거
- 링크가 업로드 URL로 치환됨
- 유튜브 문법이 embed HTML로 정규화됨

### 실행 결과
- 일부 실패 시 나머지 성공
- 자동 생성/자동 업로드 정보 반환

## 보류할 2차 항목
- `tb_article_import_jobs`
- `tb_article_import_job_items`
- 비동기 큐
- 실패 건 재시도
- 감사 로그 상세 추적
- zip 원본 보관

## 최종 권장안 요약
- 1차 고도화의 우선순위는 `manifest 없는 zip 자동 스캔`과 `상대경로 본문 assets 자동 업로드/치환`이다.
- 유튜브는 업로드 대상이 아니라 `velog`식 Markdown 문법을 기존 embed HTML로 정규화하는 방식으로 처리한다.
- `frontmatter + Markdown 원본` 보존 정책은 유지한다.
- `tags`, `summary`는 지금처럼 원본에만 보존하고 UI 기능화는 뒤로 미룬다.
- `job 이력`, `감사 추적`, `비동기`는 2차 확장으로 분리한다.
