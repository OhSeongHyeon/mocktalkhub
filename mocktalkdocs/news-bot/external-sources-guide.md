# News Bot External Sources Guide

## 1. 문서 목적

이 문서는 뉴스봇 백오피스에서 외부 소스를 선택하고 잡을 등록할 때, 어떤 설정값이 실제 수집 결과와 글 품질에 영향을 주는지 설명한다.

이 문서는 운영자 안내용이다. 핵심은 아래 두 가지다.

- 외부 소스 설정값은 어떤 글을 가져올지 결정한다.
- 게시판/카테고리 값은 가져온 글을 어디에 적재할지 결정한다.

즉, `tag`, `username`, `owner`, `repo`, `feedUrl`, `storyType`은 외부 검색 조건이고, `targetBoardSlug`, `targetBoardName`, `targetCategoryName`은 내부 적재 기준이다.

처음 쓰는 운영자는 `starter-templates.md`를 먼저 보고, 이 문서는 세부 설명서로 참고하는 것을 권장한다.

## 2. 먼저 알아둘 점

### 2.1 외부 검색 조건과 내부 적재 기준은 다르다

아래 값들은 외부 API가 어떤 글을 돌려줄지에 직접 영향을 준다.

- `Hacker News.storyType`
- `DEV.tag`
- `DEV.username`
- `GitHub Releases.owner`
- `GitHub Releases.repo`
- `RSS.feedUrl`

아래 값들은 외부에서 어떤 글을 가져올지와는 무관하고, 가져온 글을 Mocktalk 안에서 어디에 저장할지만 결정한다.

- `targetBoardSlug`
- `targetBoardName`
- `targetCategoryName`
- `isAutoCreateBoard`
- `isAutoCreateCategory`

### 2.2 결과가 0건이거나 품질이 낮아질 수 있다

뉴스봇은 검색 엔진이 아니라 외부 공개 API를 그대로 사용한다. 따라서 운영자가 입력한 조건이 좁거나 애매하면 아래 현상이 생길 수 있다.

- 글이 아예 0건 조회됨
- 주제는 맞지만 너무 오래된 글이 섞임
- 기술 주제가 넓어서 게시판 성격이 흐려짐
- 공식 소식보다 개인 의견 글이 많이 들어옴
- 특정 시점엔 새 글이 없어 한동안 같은 결과만 반복됨

이 문서의 목적은 이런 상황을 운영자가 미리 예상하도록 돕는 것이다.

## 3. 소스별 요약

| 소스 | 성격 | 주제 제어 방식 | 품질 특징 | 0건 가능성 |
| --- | --- | --- | --- | --- |
| Hacker News | 기술 커뮤니티 링크 모음 | `storyType` | 반응 좋은 글을 모으기 쉬움 | 낮음 |
| DEV | 개발자 아티클 플랫폼 | `tag` 또는 `username` | 주제 제어가 쉬움 | 중간 |
| GitHub Releases | 특정 오픈소스 릴리즈 공지 | `owner`, `repo` | 공식 업데이트 성격이라 품질이 안정적 | 중간 |
| RSS/Atom | 특정 공식 블로그/피드 | `feedUrl` | 운영자가 피드를 잘 고르면 품질이 높음 | 중간 |

### 3.1 백오피스 입력 시 공통 원칙

백오피스에서 잡을 만들 때는 아래 원칙을 권장한다.

- `jobName`은 게시판 목적이 드러나게 짓기
- `sourceType`은 게시판 성격에 맞는 소스 하나만 고르기
- `sourceConfig`는 가능한 한 좁고 명확하게 설정하기
- `targetBoardSlug`는 사람이 봐도 역할이 드러나는 slug로 통일하기
- `targetCategoryName`은 운영자가 미리 정한 소수의 이름만 사용하기
- `fetchLimit`은 처음부터 크게 잡지 말고 보수적으로 시작하기
- `collectIntervalMinutes`는 소스 성격에 맞게 조절하기

운영 초반 기본 권장값은 아래처럼 시작하면 무난하다.

- `fetchLimit`: `10`
- `isAutoCreateBoard`: `false`
- `isAutoCreateCategory`: `true`

주기 기본안:

- Hacker News: `180`
- DEV: `180`
- GitHub Releases: `720` 또는 `1440`
- RSS/Atom: `180` 또는 `360`

## 4. Hacker News

### 4.1 어떤 소스인가

Hacker News는 기술, 스타트업, 서비스 런칭, 인프라, AI, 오픈소스 이야기가 넓게 섞인 커뮤니티형 소스다.

이 소스는 특정 태그로 세밀하게 주제를 고르는 방식이 아니라, 어떤 피드 타입을 볼지 선택하는 방식이다.

### 4.2 사용 가능한 설정값

- `storyType`
  - 선택값: `topstories`, `newstories`, `beststories`
  - 비워두면 기본값은 `topstories`

예시:

```json
{
  "storyType": "topstories"
}
```

### 4.3 각 값의 의미

- `topstories`
  - 가장 무난하다.
  - 이미 어느 정도 반응이 검증된 글이 올라오므로 운영 초반 품질이 안정적이다.
- `newstories`
  - 더 빠르게 새 글을 본다.
  - 대신 품질 편차가 크고, 게시판 성격이 쉽게 흐려질 수 있다.
- `beststories`
  - 반응이 좋았던 글 중심이다.
  - 하지만 최신성보다 누적 반응이 강한 글이 섞일 수 있다.

### 4.4 품질이 달라지는 이유

Hacker News는 커뮤니티 큐레이션 결과를 가져오는 구조라, 운영자가 세밀하게 주제를 제어하기 어렵다.

즉 다음 같은 특징이 있다.

- 기술 글 외에 스타트업, 창업, 서비스 운영 글도 들어온다.
- 원문 품질은 높아도 우리 게시판 주제와 완전히 맞지 않을 수 있다.
- `newstories`는 특히 노이즈가 많아질 수 있다.

### 4.5 언제 0건이 나올 수 있나

현재 구현 기준으로는 0건 가능성이 낮다. 다만 아래 경우는 항목 수가 줄 수 있다.

- 삭제된 글
- dead 처리된 글
- 본문 제목이 비어 있는 글
- story 타입이 아닌 항목

### 4.6 권장 사용처

- 개발 일반 새소식 게시판
- 테크 트렌드 게시판
- 스타트업/서비스 관찰 게시판

### 4.7 운영 권장값

- 운영 초반 기본값은 `topstories`
- 커뮤니티 성격이 이미 좁게 잡혀 있다면 Hacker News 단독 운영보다 RSS나 GitHub Releases를 우선 고려

### 4.8 백오피스 권장 입력 예시

가장 무난한 기본 예시:

```json
{
  "jobName": "개발 일반 새소식 - Hacker News",
  "sourceType": "HACKER_NEWS",
  "sourceConfig": {
    "storyType": "topstories"
  },
  "targetBoardSlug": "tech-news",
  "targetBoardName": "개발 새소식",
  "targetCategoryName": "community",
  "collectIntervalMinutes": 180,
  "fetchLimit": 10,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

스타트업/트렌드 게시판용 예시:

```json
{
  "jobName": "스타트업 트렌드 - Hacker News",
  "sourceType": "HACKER_NEWS",
  "sourceConfig": {
    "storyType": "beststories"
  },
  "targetBoardSlug": "startup-trends",
  "targetBoardName": "스타트업 트렌드",
  "targetCategoryName": "trend",
  "collectIntervalMinutes": 360,
  "fetchLimit": 8,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

운영 초반에는 아래 조합은 피하는 편이 좋다.

- `storyType = newstories`
- `fetchLimit`를 `20` 이상 크게 주는 설정
- 짧은 주기와 넓은 게시판을 동시에 사용하는 설정

이유는 글 수는 늘어도 노이즈가 빨리 늘어나기 때문이다.

## 5. DEV

### 5.1 어떤 소스인가

DEV는 개발자들이 글을 직접 올리는 아티클 플랫폼이다. 태그 기반으로 주제를 좁히기 쉽고, 특정 작성자만 따라가는 것도 가능하다.

이 4개 소스 중 주제 제어가 가장 쉬운 편이다.

### 5.2 사용 가능한 설정값

- `tag`
  - 예: `backend`, `java`, `spring`, `docker`, `devops`
- `username`
  - 특정 DEV 작성자 계정명

예시:

```json
{
  "tag": "backend"
}
```

```json
{
  "username": "ben"
}
```

### 5.3 설정값 의미

- `tag`
  - 특정 주제에 맞는 글을 모을 때 사용
  - 가장 일반적인 운영 방식
- `username`
  - 특정 작성자의 글만 모을 때 사용
  - 큐레이션된 운영에는 좋지만, 글 수가 적어질 수 있다

### 5.4 품질이 달라지는 이유

DEV는 누구나 공개 글을 올릴 수 있으므로, 태그가 같아도 글 품질 편차가 존재한다.

아래 값 선택에 따라 결과 품질이 많이 달라진다.

- 넓은 태그
  - 예: `backend`
  - 장점: 글 수가 안정적
  - 단점: 주제가 넓고 품질 편차가 크다
- 좁은 태그
  - 예: 특정 프레임워크나 라이브러리
  - 장점: 게시판 주제와 잘 맞는다
  - 단점: 새 글이 자주 없을 수 있다
- 특정 작성자
  - 장점: 일관된 성격의 글이 들어온다
  - 단점: 글 수가 적고, 작성 활동이 줄면 거의 비게 된다

### 5.5 언제 0건이 나올 수 있나

아래 경우는 충분히 0건이 가능하다.

- 존재하지 않는 `tag`
- 너무 드문 `tag`
- 존재하지 않는 `username`
- 최근 공개 글이 없는 `username`

### 5.6 운영 권장값

- 주제 게시판이면 `tag` 기반을 우선 사용
- 운영자가 특정 필자를 강하게 큐레이션하려는 경우에만 `username` 사용
- 아주 좁은 태그는 잡 하나로만 쓰지 말고, 별도 보조 소스와 함께 운영

### 5.7 권장 사용처

- 백엔드 새소식
- 자바/스프링 새소식
- 프론트엔드 새소식
- 데브옵스/인프라 팁 게시판

### 5.8 백오피스 권장 입력 예시

백엔드 게시판 기본 예시:

```json
{
  "jobName": "백엔드 새소식 - DEV",
  "sourceType": "DEV_TO",
  "sourceConfig": {
    "tag": "backend"
  },
  "targetBoardSlug": "backend-news",
  "targetBoardName": "백엔드 새소식",
  "targetCategoryName": "article",
  "collectIntervalMinutes": 180,
  "fetchLimit": 10,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

스프링 게시판 기본 예시:

```json
{
  "jobName": "스프링 새소식 - DEV",
  "sourceType": "DEV_TO",
  "sourceConfig": {
    "tag": "spring"
  },
  "targetBoardSlug": "spring-news",
  "targetBoardName": "스프링 새소식",
  "targetCategoryName": "article",
  "collectIntervalMinutes": 180,
  "fetchLimit": 8,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

자바 게시판 기본 예시:

```json
{
  "jobName": "자바 새소식 - DEV",
  "sourceType": "DEV_TO",
  "sourceConfig": {
    "tag": "java"
  },
  "targetBoardSlug": "java-news",
  "targetBoardName": "자바 새소식",
  "targetCategoryName": "article",
  "collectIntervalMinutes": 180,
  "fetchLimit": 8,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

특정 작성자 큐레이션 예시:

```json
{
  "jobName": "특정 필자 큐레이션 - DEV",
  "sourceType": "DEV_TO",
  "sourceConfig": {
    "username": "ben"
  },
  "targetBoardSlug": "curated-dev-articles",
  "targetBoardName": "큐레이션 아티클",
  "targetCategoryName": "curated",
  "collectIntervalMinutes": 360,
  "fetchLimit": 5,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

운영 초반에는 아래 조합을 피하는 편이 좋다.

- 존재 여부를 확인하지 않은 `username`
- 너무 좁거나 생소한 `tag`
- `fetchLimit`를 크게 하고 `collectIntervalMinutes`도 아주 짧게 두는 설정

운영 초반 추천 태그는 아래 정도가 무난하다.

- `backend`
- `java`
- `spring`
- `devops`
- `docker`

## 6. GitHub Releases

### 6.1 어떤 소스인가

GitHub Releases는 특정 공개 저장소의 최신 릴리즈를 가져오는 소스다. 일반 뉴스보다 공식 업데이트 공지에 가깝다.

이 소스는 글 수는 적지만 품질과 출처 명확성이 높다.

### 6.2 사용 가능한 설정값

- `owner`
- `repo`

예시:

```json
{
  "owner": "spring-projects",
  "repo": "spring-boot"
}
```

### 6.3 설정값 의미

- `owner`
  - GitHub 조직 또는 사용자명
- `repo`
  - 저장소명

이 둘이 합쳐져 하나의 정확한 저장소를 가리킨다.

### 6.4 품질이 달라지는 이유

이 소스는 품질 편차보다 “대상 저장소를 잘 고르느냐”가 핵심이다.

- 공식 프레임워크/라이브러리 저장소를 고르면 품질이 안정적이다.
- 실험용 저장소나 릴리즈 관리가 느슨한 저장소를 고르면 품질이 떨어질 수 있다.
- 최신 릴리즈만 보기 때문에 글 수는 적다.

### 6.5 언제 0건 또는 실패가 나올 수 있나

아래 경우는 결과가 없거나 호출 실패가 날 수 있다.

- 잘못된 `owner`
- 잘못된 `repo`
- 공개 저장소가 아님
- latest release가 없는 저장소
- 무인증 호출 rate limit 초과

### 6.6 운영 권장값

- 공식 프로젝트 저장소만 사용
- 너무 많은 저장소를 짧은 주기로 등록하지 않기
- 릴리즈 기반 게시판은 “빈도는 낮지만 품질이 높은 소식”으로 운영

### 6.7 권장 사용처

- 스프링 릴리즈 게시판
- Vue/React 릴리즈 게시판
- Redis/PostgreSQL 릴리즈 게시판

### 6.8 백오피스 권장 입력 예시

스프링 부트 릴리즈 예시:

```json
{
  "jobName": "스프링 부트 릴리즈",
  "sourceType": "GITHUB_RELEASES",
  "sourceConfig": {
    "owner": "spring-projects",
    "repo": "spring-boot"
  },
  "targetBoardSlug": "spring-news",
  "targetBoardName": "스프링 새소식",
  "targetCategoryName": "release",
  "collectIntervalMinutes": 720,
  "fetchLimit": 1,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

Vue 릴리즈 예시:

```json
{
  "jobName": "Vue 릴리즈",
  "sourceType": "GITHUB_RELEASES",
  "sourceConfig": {
    "owner": "vuejs",
    "repo": "core"
  },
  "targetBoardSlug": "frontend-news",
  "targetBoardName": "프론트엔드 새소식",
  "targetCategoryName": "release",
  "collectIntervalMinutes": 720,
  "fetchLimit": 1,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

Redis 릴리즈 예시:

```json
{
  "jobName": "Redis 릴리즈",
  "sourceType": "GITHUB_RELEASES",
  "sourceConfig": {
    "owner": "redis",
    "repo": "redis"
  },
  "targetBoardSlug": "infra-news",
  "targetBoardName": "인프라 새소식",
  "targetCategoryName": "release",
  "collectIntervalMinutes": 1440,
  "fetchLimit": 1,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

운영 초반에는 아래 기준을 권장한다.

- `fetchLimit`는 사실상 `1`
- `collectIntervalMinutes`는 `720` 또는 `1440`
- 공식 프로젝트만 등록

아래 조합은 피하는 편이 좋다.

- 릴리즈가 거의 없는 저장소
- 실험성 개인 저장소
- 너무 많은 repo를 아주 짧은 주기로 등록하는 설정

## 7. RSS/Atom

### 7.1 어떤 소스인가

RSS/Atom은 운영자가 특정 공식 블로그나 기술 피드 URL을 직접 지정하는 방식이다. 가장 유연하지만, 피드 선택 책임이 운영자에게 있다.

### 7.2 사용 가능한 설정값

- `feedUrl`

예시:

```json
{
  "feedUrl": "https://spring.io/blog.atom"
}
```

### 7.3 품질이 달라지는 이유

RSS/Atom은 어떤 피드를 넣느냐가 전부라고 봐도 된다.

- 공식 블로그 피드
  - 품질이 높고 출처가 명확하다
- 개인 블로그 피드
  - 운영 의도에 따라 좋을 수도 있지만 편차가 크다
- 종합 피드
  - 글 수는 많아도 게시판 성격이 흐려질 수 있다

### 7.4 언제 0건 또는 실패가 나올 수 있나

- 잘못된 `feedUrl`
- RSS/Atom 형식이 비표준적이라 파싱 실패
- 피드에 항목이 거의 없음
- 피드는 열리지만 `title/link`가 비정상적이라 유효 항목이 적음

### 7.5 운영 권장값

- 공식 블로그 피드 우선
- 도메인과 피드 성격을 운영자가 직접 확인한 뒤 등록
- 너무 범용적인 피드는 한 게시판에 바로 연결하지 않기

### 7.6 권장 사용처

- Spring 공식 블로그 게시판
- GitHub 공식 블로그 게시판
- PostgreSQL 공식 소식 게시판

### 7.7 백오피스 권장 입력 예시

Spring 공식 블로그 예시:

```json
{
  "jobName": "Spring 공식 블로그",
  "sourceType": "RSS",
  "sourceConfig": {
    "feedUrl": "https://spring.io/blog.atom"
  },
  "targetBoardSlug": "spring-news",
  "targetBoardName": "스프링 새소식",
  "targetCategoryName": "official",
  "collectIntervalMinutes": 360,
  "fetchLimit": 8,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

GitHub 공식 블로그 예시:

```json
{
  "jobName": "GitHub 공식 블로그",
  "sourceType": "RSS",
  "sourceConfig": {
    "feedUrl": "https://github.blog/feed/"
  },
  "targetBoardSlug": "dev-platform-news",
  "targetBoardName": "개발 플랫폼 새소식",
  "targetCategoryName": "official",
  "collectIntervalMinutes": 360,
  "fetchLimit": 8,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

PostgreSQL 공식 피드 예시:

```json
{
  "jobName": "PostgreSQL 공식 소식",
  "sourceType": "RSS",
  "sourceConfig": {
    "feedUrl": "https://www.postgresql.org/feeds/news.rss"
  },
  "targetBoardSlug": "database-news",
  "targetBoardName": "데이터베이스 새소식",
  "targetCategoryName": "official",
  "collectIntervalMinutes": 720,
  "fetchLimit": 6,
  "isAutoCreateBoard": false,
  "isAutoCreateCategory": true
}
```

운영 초반에는 아래 기준을 권장한다.

- 공식 사이트 피드 우선
- `collectIntervalMinutes`는 `360` 또는 `720`
- `fetchLimit`는 `6`에서 `10` 사이로 시작

아래 조합은 피하는 편이 좋다.

- 정체가 불분명한 개인 피드
- 너무 범용적인 종합 피드
- 피드 구조를 확인하지 않은 URL

## 8. 게시판 slug와 카테고리는 무엇을 바꾸나

`targetBoardSlug`, `targetBoardName`, `targetCategoryName`은 외부에서 무엇을 가져올지와는 관계가 없다.

이 값들은 아래만 결정한다.

- 게시글이 어느 게시판에 저장될지
- 카테고리가 무엇일지
- 게시판/카테고리가 없을 때 자동 생성할지

즉 다음 두 설정은 완전히 다른 역할이다.

- `DEV.tag=backend`
  - 외부에서 어떤 글을 찾을지 결정
- `targetBoardSlug=backend-news`
  - 찾은 글을 어느 게시판에 넣을지 결정

### 8.1 이 값이 잘못되면 생길 수 있는 문제

- 외부 수집은 성공했는데 내부 게시판이 없어 적재 실패
- 자동 생성이 켜져 있어 의도하지 않은 게시판이 새로 생김
- 카테고리명이 일관되지 않아 같은 주제 글이 여러 카테고리로 흩어짐

## 9. 운영 기준 권장안

운영 초반에는 분류를 외부 소스가 만들게 두지 않는 것이 좋다.

권장 기준:

- `1 잡 = 1 게시판` 원칙 사용
- 게시판 자동 생성은 기본 `off`
- 카테고리는 운영자가 미리 정한 이름만 사용
- 외부 태그명을 그대로 카테고리명으로 무한 생성하지 않기
- GitHub Releases와 공식 RSS를 우선 사용
- DEV와 Hacker News는 보조 소스로 사용

## 10. 추천 조합 예시

### 10.1 스프링 새소식 게시판

- 외부 소스: `GITHUB_RELEASES`
- 설정:

```json
{
  "owner": "spring-projects",
  "repo": "spring-boot"
}
```

- 게시판 slug: `spring-news`
- 카테고리: `release`

보조 잡:

- 외부 소스: `RSS`
- 설정:

```json
{
  "feedUrl": "https://spring.io/blog.atom"
}
```

### 10.2 백엔드 새소식 게시판

- 외부 소스: `DEV_TO`
- 설정:

```json
{
  "tag": "backend"
}
```

- 게시판 slug: `backend-news`
- 카테고리: `article`

보조 잡:

- 외부 소스: `HACKER_NEWS`
- 설정:

```json
{
  "storyType": "topstories"
}
```

### 10.3 운영 초반에 바로 쓰기 좋은 추천 조합

운영 초반에 품질과 안정성을 같이 보려면 아래 조합이 무난하다.

- 스프링 새소식
  - 주 잡: `GITHUB_RELEASES / spring-projects / spring-boot`
  - 보조 잡: `RSS / https://spring.io/blog.atom`
- 백엔드 새소식
  - 주 잡: `DEV_TO / tag=backend`
  - 보조 잡: `HACKER_NEWS / topstories`
- 인프라 새소식
  - 주 잡: `GITHUB_RELEASES / redis / redis`
  - 보조 잡: `RSS / PostgreSQL 또는 다른 공식 피드`

운영 초반엔 하나의 게시판에 잡을 너무 많이 연결하지 말고, `주 잡 1개 + 보조 잡 1개` 정도로 시작하는 편이 좋다.

## 11. 자주 발생할 수 있는 오해

### 11.1 게시판 slug를 바꾸면 더 좋은 글을 찾을 수 있나

아니다. 게시판 slug는 내부 저장 위치만 바꾼다.

### 11.2 카테고리를 바꾸면 외부 검색 조건도 바뀌나

아니다. 카테고리는 내부 분류값이다.

### 11.3 잡 등록 직후 글이 없으면 버그인가

버그가 아닐 수 있다. 외부 조건이 너무 좁거나, 해당 시점에 새 글이 없을 수 있다.

### 11.4 글 품질이 낮으면 스케줄 주기를 늘리면 해결되나

항상 그렇지는 않다. 품질 문제는 대체로 소스 선택이나 검색 조건 문제다. 주기 변경은 빈도 조절에는 도움이 되지만 품질을 직접 올리진 않는다.

## 12. 백오피스 UX 세분화 가이드

현재 뉴스봇 폼은 하나의 긴 폼이지만, 운영자 입장에선 아래 다섯 구역으로 이해하는 편이 가장 헷갈리지 않는다.

- 공통 정보
- 외부 소스 조건
- 내부 적재 정보
- 실행 정책
- 자동 생성 정책

이 섹션은 실제 폼 필드 기준으로 어떤 문구와 기본값을 주는 게 좋은지 설명한다.

### 12.1 공통 정보 구역

필드:

- `jobName`
- `sourceType`

권장 문구:

- `jobName`
  - placeholder: `예: 스프링 부트 릴리즈`
- `sourceType`
  - 도움말: `어떤 외부 소스에서 글을 가져올지 선택합니다.`

### 12.2 외부 소스 조건 구역

이 구역은 `sourceType`에 따라 필드가 달라진다.

#### Hacker News

- 컨트롤 타입: `select`
- 필드: `storyType`
- 권장 기본 선택값: `topstories`
- 도움말: `반응이 검증된 글은 topstories, 더 빠른 글은 newstories, 누적 인기글은 beststories`

권장 UI:

- `Top Stories`
- `New Stories`
- `Best Stories`

#### DEV

현재 구현은 아래처럼 세분화되어 있다.

- 컨트롤 타입: `radio` 또는 `segmented control`
- 필드: `mode`
  - `tag 기준`
  - `작성자 기준`

현재 동작:

- `mode = tag`면 `tag` input만 노출
- `mode = username`이면 `username` input만 노출

권장 문구:

- `mode`
  - 도움말: `태그로 넓게 모을지, 특정 작성자만 모을지 고릅니다.`
- `tag`
  - placeholder: `예: backend`
- `username`
  - placeholder: `예: ben`

권장 기본값:

- mode: `tag 기준`
- tag: `backend`

#### GitHub Releases

- 필드: `owner`, `repo`
- 권장 문구:
  - `owner`
    - placeholder: `예: spring-projects`
  - `repo`
    - placeholder: `예: spring-boot`
- 도움말: `공개 저장소의 최신 릴리즈 1건을 기준으로 가져옵니다.`

#### RSS/Atom

- 필드: `feedUrl`
- 권장 문구:
  - placeholder: `예: https://spring.io/blog.atom`
- 도움말: `공식 블로그나 공지 피드 URL을 넣는 것을 권장합니다.`

### 12.3 내부 적재 정보 구역

필드:

- `targetBoardSlug`
- `targetBoardName`
- `targetCategoryName`

권장 문구:

- `targetBoardSlug`
  - placeholder: `예: spring-news`
  - 도움말: `가져온 글을 저장할 게시판 slug입니다.`
- `targetBoardName`
  - placeholder: `예: 스프링 새소식`
  - 도움말: `게시판 자동 생성 시 사용할 이름입니다.`
- `targetCategoryName`
  - placeholder: `예: release`
  - 도움말: `게시판 안에서 글을 분류할 기본 카테고리입니다.`

권장 UX:

- `targetBoardName`은 `게시판 자동 생성 허용`을 켰을 때만 강조 표시
- `targetBoardSlug`와 `targetBoardName` 근처에 `외부 검색 조건이 아니라 내부 저장 위치입니다` 문구를 함께 노출

### 12.4 실행 정책 구역

필드:

- `collectIntervalMinutes`
- `fetchLimit`
- `timezone`

권장 문구:

- `collectIntervalMinutes`
  - 기본값: 소스별 추천값 사용
  - 도움말: `분 단위 수집 주기입니다. 예: 180=3시간, 1440=24시간`
- `fetchLimit`
  - 기본값: 소스별 추천값 사용
  - 도움말: `한 번 실행할 때 가져올 최대 글 수입니다.`
- `timezone`
  - 기본값: `Asia/Seoul`
  - 도움말: `기본값 그대로 두는 경우가 대부분입니다.`

권장 UX:

- `collectIntervalMinutes`는 추천 버튼 또는 select 제공
  - `60`, `180`, `360`, `720`, `1440`
- `fetchLimit`도 추천 버튼 제공
  - `1`, `5`, `10`, `20`
- `timezone`은 고급 설정으로 접어도 됨

### 12.5 자동 생성 정책 구역

필드:

- `autoCreateBoard`
- `autoCreateCategory`

권장 기본 상태:

- `autoCreateBoard = false`
- `autoCreateCategory = true`

권장 문구:

- `autoCreateBoard`
  - 도움말: `대상 게시판이 없을 때 자동 생성합니다. 운영 초반에는 기본적으로 끄는 편이 안전합니다.`
- `autoCreateCategory`
  - 도움말: `대상 카테고리가 없을 때 자동 생성합니다.`

### 12.6 소스별 추천 기본값

현재 폼도 아래 권장값에 맞춰 시작하는 것을 기준으로 한다.

| 소스 | 외부 조건 기본값 | 권장 주기(분) | 권장 fetchLimit |
| --- | --- | --- | --- |
| Hacker News | `storyType = topstories` | `180` | `10` |
| DEV | `mode = tag`, `tag = backend` | `180` | `10` |
| GitHub Releases | `owner = spring-projects`, `repo = spring-boot` | `720` | `1` |
| RSS | `feedUrl = https://spring.io/blog.atom` | `360` | `8` |

### 12.7 운영자에게 바로 보이면 좋은 보조 문구

폼에 아래 문구가 보이면 오해를 줄일 수 있다.

- `외부 소스 조건은 어떤 글을 가져올지 결정합니다.`
- `대상 게시판/카테고리는 가져온 글을 어디에 저장할지 결정합니다.`
- `게시판 자동 생성은 기본적으로 꺼두는 편이 안전합니다.`
- `DEV는 tag와 username 중 하나만 사용하는 것을 권장합니다.`

### 12.8 필수 입력 하이라이트

현재 백오피스 폼은 필수 입력이 비어 있으면 상단 메시지만 띄우지 않고 해당 입력 필드도 함께 하이라이트한다.

주요 대상:

- `jobName`
- `targetBoardSlug`
- `DEV`의 `tag` 또는 `username`
- `GitHub Releases`의 `owner`, `repo`
- `RSS`의 `feedUrl`
- `autoCreateBoard = true`일 때 `targetBoardName`

## 13. 운영자 체크리스트

잡을 만들기 전에 아래를 확인하는 것을 권장한다.

- 이 소스는 공식 소식용인가, 커뮤니티 글 모음용인가
- 입력한 `tag`, `username`, `owner`, `repo`, `feedUrl`가 실제로 유효한가
- 이 잡은 어떤 게시판 하나에만 적재되도록 설계됐는가
- 게시판 자동 생성이 정말 필요한가
- 카테고리명을 운영 기준에 맞게 통일했는가
- 글 수보다 품질이 중요한 게시판인지, 반대로 글 수가 더 중요한 게시판인지
