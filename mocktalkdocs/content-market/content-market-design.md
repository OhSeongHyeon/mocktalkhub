# 콘텐츠 / 환율·금 시세 설계서

## 문서 목적

- `콘텐츠` 허브와 `환율/금 시세` 기능의 현재 구현 구조를 정리한다.
- 실제 데이터 흐름, 저장 구조, 운영 흐름을 코드 기준으로 기록한다.
- 자동 수집, 공개 조회, 관리자 운영 기능의 책임 경계를 명확히 남긴다.

## 1. 현재 구현 요약

- 프론트는 외부 시세 API를 직접 호출하지 않고 백엔드 공개 API만 사용한다.
- 백엔드는 일간 스냅샷을 `tb_market_snapshots`에 적재하고 시계열 API로 재가공해 제공한다.
- 런타임 수집 대상은 `USD_KRW`, `EUR_KRW`, `JPY_KRW`, `XAU_USD` 4개 원천 종목이며 `XAU_KRW`는 백엔드에서 파생 계산한다.
- 공개 화면은 `콘텐츠 허브 -> 환율/금 시세 상세` 구조로 분리되어 있다.
- 운영 화면은 `지금 최신화`, `CSV/XLSX 임포트` 두 기능을 별도 관리자 API로 제공한다.
- 실시간 스트리밍 대신 `백엔드 일일 수집 + 상세 화면 30분 폴링`을 사용한다.

## 2. 상위 아키텍처

1. `YahooFinanceMarketQuoteClient`
2. `MarketSnapshotCollectorService`
3. `tb_market_snapshots`
4. `ContentMarketService`
5. `ContentMarketSeriesCacheStore`
6. 공개 화면 `/contents`, `/contents/market`
7. 관리자 화면 `/admin/content-market`

## 3. 데이터 흐름

### 3.1 자동 수집 흐름

1. `ContentMarketScheduler`가 기본 cron `0 5 3 * * *`, 시간대 `Asia/Seoul`로 실행된다.
2. 기능이 활성화돼 있으면 `MarketSnapshotCollectorService.collectLatestSnapshots()`를 호출한다.
3. 수집 서비스는 `MarketInstrumentCode.rawTargets()` 기준으로 Yahoo Finance 현재 시세를 조회한다.
4. `XAU_USD`, `USD_KRW`가 모두 존재하면 `XAU_KRW = XAU_USD * USD_KRW`로 파생 시세를 만든다.
5. 각 종목은 `instrument_code + observed_at` 기준으로 upsert 저장된다.
6. `CREATED`, `UPDATED`가 발생한 종목의 장기 preset 시계열 캐시를 비운다.

### 3.2 시작 시 1회 수집

- `ApplicationReadyEvent` 시점에 기능이 활성화돼 있고 `startupCollectEnabled=true`면 수집을 1회 더 시도한다.
- 초기 배포 직후 데이터 공백을 줄이기 위한 보조 장치다.

### 3.3 공개 조회 흐름

1. 상세 화면 진입 시 `GET /api/contents/market/overview`를 먼저 호출한다.
2. 기본 기간 `YEAR` 기준으로 표시 대상 5종목의 series API를 병렬 호출한다.
3. 프론트는 통합 그래프용 상대지수와 선택 종목 상세 카드/통계를 화면에서 계산한다.
4. 페이지가 열려 있는 동안 30분마다 동일한 공개 API를 다시 호출한다.

### 3.4 수동 최신화 흐름

1. 관리자 화면에서 `지금 최신화`를 실행한다.
2. `POST /api/admin/contents/market/refresh`가 동일한 수집 서비스를 즉시 1회 실행한다.
3. 응답에는 실행 시각, 생성/갱신/스킵 건수, 종목별 처리 결과가 포함된다.

### 3.5 파일 임포트 흐름

1. 관리자 화면에서 `.csv` 또는 `.xlsx` 파일을 업로드한다.
2. `MarketSnapshotImportService`가 통합 파일 또는 종목별 파일 규칙으로 파싱한다.
3. 각 row는 `instrument_code`, `observed_at`, `price_value`를 검증한 뒤 `MANUAL_IMPORT` 공급자명으로 upsert 저장된다.
4. 임포트 완료 후 영향 종목 전체의 `change_value`, `change_rate`를 재계산한다.
5. 영향 종목의 장기 preset 시계열 캐시를 삭제하고 집계 결과를 반환한다.

## 4. 외부 데이터 소스 전략

### 4.1 런타임 수집

현재 런타임 구현은 Yahoo Finance 단일 소스를 사용한다.

- `USD_KRW` -> `USDKRW=X`
- `EUR_KRW` -> `EURKRW=X`
- `JPY_KRW` -> `JPYKRW=X`
- `XAU_USD` -> `GC=F`

`XAU_KRW`는 외부에서 직접 조회하지 않고 내부 파생값으로 만든다.

### 4.2 백필 데이터셋 생성

운영용 런타임 수집과 과거 백필용 데이터셋 생성은 분리돼 있다.

- 환율 백필: Frankfurter
- 금 시세 백필: Yahoo Finance chart API
- `XAU_KRW` 백필: `XAU_USD * 가장 가까운 직전 USD_KRW`

## 5. 갱신 전략

### 5.1 백엔드

- 기본 수집 주기: 하루 1회
- 기본 cron: `0 5 3 * * *`
- 기본 시간대: `Asia/Seoul`
- 앱 시작 시 1회 수집: 활성화 가능

### 5.2 프론트

- 상세 화면 진입 시 overview 1회 조회
- 기본 기간 `1년` series 1회 조회
- 상세 화면이 열려 있는 동안 30분 간격 폴링
- 상단 `새로고침` 버튼은 관리자 최신화가 아니라 공개 API 재조회 버튼

### 5.3 실시간 스트리밍 비채택

- 초단위 tick 데이터가 필요한 화면이 아니다.
- 무료 운영과 단순한 장애 대응을 우선한다.
- 현재 범위에서는 `SSE`, `WebSocket`을 사용하지 않는다.

## 6. 저장 구조

### 6.1 테이블

- `tb_market_snapshots`

주요 컬럼:

- `market_snapshot_id`
- `instrument_code`
- `market_group`
- `provider_name`
- `base_currency`
- `quote_currency`
- `price_value`
- `change_value`
- `change_rate`
- `observed_at`
- `created_at`
- `updated_at`

### 6.2 중복 기준

- DB 제약과 서비스 upsert 기준은 모두 `instrument_code + observed_at`이다.
- 동일 시각에 공급자명이 달라져도 기존 row를 갱신한다.

### 6.3 보관 정책

- 원본 스냅샷은 장기 보관 전제로 운영한다.
- 현재 종목 수와 일간 적재 밀도 기준으로 장기 보관 부담이 크지 않다.
- 과거 데이터 보강은 외부 히스토리 재조회보다 파일 임포트를 우선한다.

## 7. 백엔드 설계

### 7.1 주요 패키지

- `domain/content/controller`
- `domain/content/service`
- `domain/content/entity`
- `domain/content/repository`
- `domain/content/config`
- `infra/market`

### 7.2 핵심 서비스

- `YahooFinanceMarketQuoteClient`: 원천 종목 시세 조회
- `MarketSnapshotCollectorService`: 자동 수집, 수동 최신화 공통 처리
- `MarketSnapshotCommandService`: upsert, 변동값 재계산
- `ContentMarketService`: overview, series 조회
- `ContentMarketSeriesCacheStore`: 장기 preset 시계열 Redis 캐시
- `MarketSnapshotImportService`: CSV/XLSX 파싱과 row 검증
- `AdminContentMarketService`: 최신화/임포트 운영 API 집계 응답

### 7.3 공개 API

- `GET /api/contents/market/overview`
- `GET /api/contents/market/series?instrument=USD_KRW&period=MONTH`
- `GET /api/contents/market/series?instrument=USD_KRW&period=CUSTOM&startDate=2026-01-01&endDate=2026-03-15`

`period`는 `TEN_YEAR`, `FIVE_YEAR`, `THREE_YEAR`, `YEAR`, `HALF_YEAR`, `QUARTER`, `MONTH`, `WEEK`, `CUSTOM`를 지원한다.

### 7.4 운영 API

- `POST /api/admin/contents/market/refresh`
- `POST /api/admin/contents/market/import`

관리자 API는 `ADMIN`, `MANAGER` 권한을 요구한다.

## 8. 프론트 설계

### 8.1 라우트

- `/contents`
- `/contents/market`
- `/admin/content-market`

### 8.2 허브 화면

- `이미지 갤러리` 카드: 준비중 상태
- `환율/금 시세` 카드: 상세 화면 진입

### 8.3 상세 화면

- 마지막 갱신 시각
- `10년 / 5년 / 3년 / 1년 / 6개월 / 3개월 / 30일 / 7일`
- 직접 기간 선택
- 전체 종목 상대지수 통합 그래프
- 종목 선택 카드 5개
- 선택 종목 단일 그래프
- 기간 평균/중위값/최저값/최고값

금 시세는 원천 데이터가 1트로이온스 기준이지만 화면에서는 `/g` 단위로 변환해 보여준다.

### 8.4 관리자 화면

- 최신화 실행 버튼
- 통합 파일 / 종목별 파일 모드 전환
- CSV/XLSX 업로드
- 처리 결과 카드
- 실패 row 상위 20건 노출

## 9. 캐시 설계

- 캐시 대상: `YEAR`, `THREE_YEAR`, `FIVE_YEAR`, `TEN_YEAR`
- 캐시 키: `content:market:series:v1:{instrument}:{period}`
- 기본 TTL: `86400초`
- 캐시 비대상: `HALF_YEAR`, `QUARTER`, `MONTH`, `WEEK`, `CUSTOM`
- 최신화, 자동 수집, 임포트 후 영향 종목만 명시적으로 무효화

## 10. 후속 고도화 후보

- 임포트 작업 이력 저장
- 임포트 템플릿 다운로드
- 추가 종목 확대
- 수집 상태 모니터링
- 이미지 갤러리 실제 구현
