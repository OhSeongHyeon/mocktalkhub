# 콘텐츠 시세 캐싱 전략

## 1. 목적

`GET /api/contents/market/series` 중 장기 기간 조회는 row 수와 응답 직렬화 비용이 상대적으로 크다.
수집 주기가 하루 1회이기 때문에 장기 preset 기간은 Redis 캐시 효율이 높다.

이 문서는 현재 구현된 Redis 캐시 전략을 정리한다.

## 2. 핵심 원칙

- 캐시는 `series` 조회에만 적용한다.
- 장기 preset 기간만 캐시한다.
- 쓰기 작업 후에는 TTL만 기다리지 않고 영향 종목 키를 즉시 삭제한다.
- 캐시가 비활성화되거나 역직렬화에 실패해도 DB fallback이 가능해야 한다.

## 3. 캐시 대상

### 3.1 대상 API

- `GET /api/contents/market/series`

### 3.2 실제 캐시 대상 기간

- `YEAR`
- `THREE_YEAR`
- `FIVE_YEAR`
- `TEN_YEAR`

### 3.3 캐시 비대상 기간

- `HALF_YEAR`
- `QUARTER`
- `MONTH`
- `WEEK`
- `CUSTOM`

`CUSTOM`은 날짜 조합이 다양해 키 폭증과 무효화 복잡도가 커지므로 제외한다.

## 4. 구현 요소

- 클래스: `ContentMarketSeriesCacheStore`
- 저장 방식: `StringRedisTemplate`
- 직렬화: `ObjectMapper`
- 캐시 키 prefix: `content:market:series:v1:`

## 5. Redis 키 설계

키 형식:

```text
content:market:series:v1:{instrument}:{period}
```

예시:

```text
content:market:series:v1:USD_KRW:YEAR
content:market:series:v1:XAU_USD:TEN_YEAR
content:market:series:v1:XAU_KRW:FIVE_YEAR
```

규칙:

- `instrument`, `period`는 enum 문자열 그대로 사용한다.
- 응답 구조가 바뀌면 prefix 버전을 올려 강제 무효화할 수 있다.

## 6. 저장 값과 TTL

- 저장 값: `MarketSeriesResponse` JSON 문자열
- 기본 TTL: `86400초`

제어 프로퍼티:

- `CONTENT_MARKET_SERIES_CACHE_ENABLED`
- `CONTENT_MARKET_SERIES_CACHE_TTL_SECONDS`

`seriesCacheEnabled=false` 또는 `seriesCacheTtlSeconds <= 0`이면 캐시를 사용하지 않는다.

## 7. 조회 흐름

1. `ContentMarketService.findSeries()`가 기간을 해석한다.
2. 기간이 캐시 대상이면 `ContentMarketSeriesCacheStore.find()`를 먼저 호출한다.
3. cache hit면 역직렬화 후 즉시 반환한다.
4. cache miss면 DB에서 시계열을 조회해 `MarketSeriesResponse`를 만든다.
5. 생성된 응답이 캐시 대상 기간이면 Redis에 저장한다.

역직렬화 실패 시 해당 키를 즉시 삭제하고 DB 조회로 fallback한다.

## 8. 무효화 전략

### 8.1 자동 수집 / 관리자 최신화

대상:

- `ContentMarketScheduler`
- `POST /api/admin/contents/market/refresh`

동작:

- `MarketSnapshotCollectorService`가 수집 결과 중 `CREATED`, `UPDATED` 상태 종목만 추린다.
- `SKIPPED` 종목은 무효화 대상에서 제외한다.
- 영향 종목의 장기 preset 키를 일괄 삭제한다.

`XAU_KRW`는 파생 종목이므로 실제로 저장 결과가 생긴 경우 함께 무효화된다.

### 8.2 임포트

대상:

- `POST /api/admin/contents/market/import`

동작:

- 임포트에 포함된 종목 집합을 수집한다.
- `recalculateChanges()` 수행 후 해당 종목의 장기 preset 키를 삭제한다.
- 실패 row만 있거나 영향 종목이 없으면 삭제하지 않는다.

## 9. 현재 비적용 영역

- `overview` 응답 캐시
- 단기 기간 캐시
- `CUSTOM` 기간 캐시

현재 구현은 `findSeries` 캐시에만 집중한다.

## 10. 후속 고려사항

- `CUSTOM` 캐시가 필요하면 날짜 범위 정규화 규칙을 먼저 정해야 한다.
- 장기적으로 포인트 수가 더 늘어나면 downsampling 전략을 검토한다.
- overview가 병목이 되면 별도 캐시 도입을 재검토한다.
