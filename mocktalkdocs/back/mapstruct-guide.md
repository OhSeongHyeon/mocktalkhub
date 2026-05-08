# MapStruct 사용 가이드

이 프로젝트는 MapStruct로 엔티티와 DTO 간 단순 매핑을 분리하고, 연관 엔티티 주입이나 생성 규칙은 `default` 메서드와 서비스 레이어에서 처리합니다.

## 현재 적용 상태

- 의존성
  - `org.mapstruct:mapstruct:1.6.3`
  - `org.mapstruct:mapstruct-processor:1.6.3`
  - `lombok-mapstruct-binding:0.2.0`
- 공통 설정
  - `mocktalkback/src/main/java/com/mocktalkback/global/config/MapstructConfig.java`
- 현재 매퍼
  - `domain/article/mapper/ArticleMapper`
  - `domain/board/mapper/BoardMapper`
  - `domain/comment/mapper/CommentMapper`
  - `domain/file/mapper/FileMapper`

## 기본 규칙

- 공통 설정은 `MapstructConfig` 를 사용한다.
- 매퍼는 도메인 패키지 안에 둔다.
- 단순 필드 매핑은 MapStruct 어노테이션으로 처리한다.
- 연관 엔티티가 필요한 생성 매핑은 `default` 메서드로 처리한다.
- 권한, 렌더링, 정합성 검사는 매퍼가 아니라 서비스가 담당한다.
- `unmappedTargetPolicy = ERROR` 를 유지해 매핑 누락을 빌드 단계에서 잡는다.

## 공통 설정

현재 공통 설정은 아래와 같다.

```java
package com.mocktalkback.global.config;

import org.mapstruct.MapperConfig;
import org.mapstruct.ReportingPolicy;

@MapperConfig(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.ERROR
)
public interface MapstructConfig {
}
```

## 실제 매퍼 패턴

### 1. 단순 응답 매핑

예시: `ArticleMapper`

```java
@Mapper(config = MapstructConfig.class)
public interface ArticleMapper {

    @Mapping(target = "boardId", source = "board.id")
    @Mapping(target = "userId", source = "user.id")
    @Mapping(target = "categoryId", source = "category.id")
    ArticleResponse toResponse(ArticleEntity entity);
}
```

### 2. 연관 엔티티가 필요한 생성 매핑

게시글 생성은 요청 DTO만으로 끝나지 않기 때문에 서비스가 `board`, `user`, `category` 를 조회해서 넘긴다.

```java
default ArticleEntity toEntity(
    ArticleCreateRequest request,
    BoardEntity board,
    UserEntity user,
    ArticleCategoryEntity category
) {
    return ArticleEntity.builder()
        .board(board)
        .user(user)
        .category(category)
        .visibility(request.visibility())
        .title(request.title())
        .content(request.contentSource())
        .contentSource(request.contentSource())
        .contentFormat(request.contentFormat())
        .hit(0L)
        .notice(request.notice())
        .build();
}
```

현재 코드 기준으로 게시글 본문은 `contentSource`, `contentFormat` 을 함께 다룬다. 예전처럼 `request.content()` 단일 필드 예시로 보면 현재 구현과 맞지 않는다.

### 3. 보조 응답 조합

`BoardMapper` 처럼 파일 응답이나 owner 표시명 같은 부가 정보를 함께 조합하는 경우에는 `default` 메서드로 DTO를 직접 생성한다.

예시:

- `BoardMapper.toResponse(BoardEntity entity, FileResponse boardImage)`
- `BoardMapper.toDetailResponse(...)`

즉, “MapStruct generated mapping + 수동 조합용 default 메서드” 혼합 패턴을 실제로 사용하고 있다.

## 서비스에서의 사용 흐름

서비스는 다음 순서를 따른다.

1. 인증 사용자, 연관 엔티티, 권한을 확인한다.
2. 필요하면 본문 렌더링이나 정규화 같은 전처리를 한다.
3. 매퍼를 호출해 엔티티 또는 응답 DTO를 만든다.
4. 저장/후처리를 수행한다.

게시글 생성 흐름은 현재 대략 아래 패턴이다.

```java
ArticleContentService.RenderedContent renderedContent = articleContentService.render(
    request.contentSource(),
    request.contentFormat()
);

ArticleCreateRequest sanitizedRequest = new ArticleCreateRequest(
    request.boardId(),
    actorUserId,
    request.categoryId(),
    request.visibility(),
    request.title(),
    renderedContent.contentSource(),
    request.contentFormat(),
    request.notice(),
    request.fileIds()
);

ArticleEntity entity = articleMapper.toEntity(sanitizedRequest, board, user, category);
```

즉, 매퍼는 “이미 검증/정규화된 값”을 받아 조립하는 역할이다.

## 사용 원칙

### 매퍼가 맡는 것

- 엔티티 -> 응답 DTO
- 요청 DTO + 연관 엔티티 -> 새 엔티티 조립
- 단순 필드 이름 차이 보정

### 매퍼가 맡지 않는 것

- 권한 검사
- DB 조회
- HTML/Markdown 렌더링
- 첨부파일 동기화
- 엔티티 수정 정책

엔티티 업데이트는 지금도 매퍼보다 엔티티 메서드나 서비스 로직으로 처리하는 경우가 많다.

## 주의할 점

- Lombok builder 를 쓰는 엔티티는 `lombok-mapstruct-binding` 설정이 빠지면 빌드 문제가 날 수 있다.
- 새 필드를 DTO나 엔티티에 추가하면 `unmappedTargetPolicy = ERROR` 때문에 매퍼를 함께 수정해야 한다.
- 연관 엔티티를 ID만으로 매핑하지 않는다. 서비스가 실제 엔티티를 조회해서 넘기는 현재 패턴을 유지하는 편이 안전하다.
- Board 상세처럼 외부 값(`boardImage`, `ownerDisplayName`, `subscribed`)이 필요한 응답은 generated mapping 하나로 해결하려고 하지 않는다.

## 참고 파일

- `mocktalkback/build.gradle`
- `mocktalkback/src/main/java/com/mocktalkback/global/config/MapstructConfig.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/article/mapper/ArticleMapper.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/board/mapper/BoardMapper.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/comment/mapper/CommentMapper.java`
- `mocktalkback/src/main/java/com/mocktalkback/domain/file/mapper/FileMapper.java`
