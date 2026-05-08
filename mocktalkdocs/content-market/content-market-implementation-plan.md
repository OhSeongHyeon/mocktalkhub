# 콘텐츠 / 환율·금 시세 작업계획 및 완료 현황

## 문서 목적

- `콘텐츠` 허브와 `환율/금 시세` 기능의 구현 범위를 현재 시점 기준으로 정리한다.
- 초기에 잡았던 작업 계획 중 무엇이 실제로 반영됐는지 기록한다.
- 남은 후속 과제를 별도로 정리해 다음 작업 기준점으로 사용한다.

## 1. 기준 시점

- 기준일: `2026-03-15`
- 기준 저장소: `mocktalkfront`, `mocktalkback`
- 범위: 공개 콘텐츠 화면, 관리자 운영 화면, 백필 데이터셋 문서/스크립트

## 2. 1차 범위 완료 현황

완료:

- 사이드 메뉴 `콘텐츠` 반영
- `/contents` 허브 화면
- `이미지 갤러리(준비중)` 카드
- `/contents/market` 상세 화면
- `tb_market_snapshots` 마이그레이션
- 외부 시세 수집 스케줄러
- 공개 `overview`, `series` API
- 장기 preset 기간 Redis 캐시
- `/admin/content-market` 운영 화면
- 백오피스 `지금 최신화`
- 백오피스 `CSV/XLSX 임포트`
- 백필 데이터셋 생성 스크립트와 CSV 산출물

제외 상태 유지:

- 외부 API 재조회 방식 백필
- 이미지 갤러리 실제 기능
- 실시간 스트리밍
- 관심종목/알림

## 3. 실제 구현 내용

### 3.1 백엔드

- `V14__content_market_snapshots.sql`로 시세 스냅샷 테이블을 생성했다.
- 런타임 외부 소스는 `YahooFinanceMarketQuoteClient` 단일 구현을 사용한다.
- 원천 수집 종목은 `USD_KRW`, `EUR_KRW`, `JPY_KRW`, `XAU_USD`이고 `XAU_KRW`는 내부 파생값이다.
- `ContentMarketScheduler`는 기본 cron `0 5 3 * * *`, 시간대 `Asia/Seoul`로 동작한다.
- 앱 시작 시 `startupCollectEnabled=true`면 1회 수집을 시도한다.
- `ContentMarketService`가 공개 overview/series 조회를 담당한다.
- `ContentMarketSeriesCacheStore`가 `YEAR`, `THREE_YEAR`, `FIVE_YEAR`, `TEN_YEAR`만 캐시한다.
- `AdminContentMarketService`가 최신화/임포트 집계 응답과 캐시 무효화를 처리한다.

### 3.2 프론트

- `ContentHubPage.vue`에서 준비중 카드와 실제 진입 카드 2개를 노출한다.
- `ContentMarketPage.vue`는 overview 조회 후 전체 종목 series를 병렬 조회한다.
- 기본 조회 기간은 `1년`이다.
- 상세 화면은 30분 간격 폴링을 사용한다.
- 금 시세는 1트로이온스 원본값을 `/g`로 환산해 노출한다.
- `AdminContentMarketPage.vue`는 최신화, 통합/종목별 임포트, 실패 row 요약을 제공한다.

### 3.3 테스트 및 보조 자산

- 백엔드 테스트:
  - `ContentMarketServiceTest`
  - `AdminContentMarketServiceTest`
  - `MarketSnapshotCommandServiceTest`
  - `MarketSnapshotImportServiceTest`
  - `ContentMarketControllerTest`
  - `AdminContentMarketControllerTest`
- 프론트 테스트:
  - `contentMarketApi.test.ts`
  - `adminContentMarketApi.test.ts`
- 백필 스크립트:
  - `mocktalkback/scripts/content_market_backfill_dataset.py`

## 4. 운영 기준

- 공개 API:
  - `GET /api/contents/market/overview`
  - `GET /api/contents/market/series`
- 관리자 API:
  - `POST /api/admin/contents/market/refresh`
  - `POST /api/admin/contents/market/import`
- 관리자 권한: `ADMIN`, `MANAGER`
- 과거 데이터 보강: 백오피스 업로드 또는 백필 CSV 사용

## 5. 남은 후속 과제

- 이미지 갤러리 실제 기능 구현
- 임포트 작업 이력 저장
- 임포트 템플릿 다운로드
- 추가 종목 확대
- 수집 상태 모니터링 및 운영 알림
