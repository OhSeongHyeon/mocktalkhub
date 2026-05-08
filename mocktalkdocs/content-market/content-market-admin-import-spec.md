# 콘텐츠 / 환율·금 시세 백오피스 운영 기능 정의서

## 문서 목적

- 백오피스에서 제공하는 `지금 최신화`, `CSV/XLSX 임포트` 기능의 실제 동작을 정리한다.
- 관리자 엔드포인트, 입력 형식, 응답 필드, 검증 규칙을 코드 기준으로 명확히 남긴다.

## 1. 기능 개요

백오피스 운영 기능은 아래 2개로 구성된다.

- `지금 최신화`
- `시세 데이터 임포트`

화면 경로는 `/admin/content-market`, API prefix는 `/api/admin/contents/market`이다.

## 2. 권한 정책

- 컨트롤러 권한: `@PreAuthorize("hasAnyRole('ADMIN','MANAGER')")`
- 공개 콘텐츠 API와 분리된 관리자 전용 엔드포인트를 사용한다.

## 3. 지금 최신화

### 3.1 엔드포인트

- `POST /api/admin/contents/market/refresh`

### 3.2 목적

- 현재 시세를 즉시 다시 수집한다.
- 일일 스케줄러를 기다리지 않고 운영자가 최신 데이터를 반영할 수 있게 한다.

### 3.3 입력

- 별도 request body 없음

### 3.4 처리 방식

- `MarketSnapshotCollectorService.collectLatestSnapshots()`를 그대로 재사용한다.
- 자동 수집과 동일한 원천 종목 조회, 파생값 계산, upsert, 캐시 무효화 규칙을 따른다.

### 3.5 응답 필드

- `executedAt`
- `totalCount`
- `createdCount`
- `updatedCount`
- `skippedCount`
- `items`

`items` 원소 필드:

- `instrumentCode`
- `observedAt`
- `status`

현재 최신화 응답에는 별도 `failedCount` 필드가 없다.

## 4. 시세 데이터 임포트

### 4.1 엔드포인트

- `POST /api/admin/contents/market/import`

### 4.2 입력

- multipart `file`
- 선택 query param `instrument`

`instrument`가 없으면 통합 파일 모드, 있으면 종목별 파일 모드로 처리한다.

### 4.3 허용 파일 형식

- `.csv`
- `.xlsx`

지원하지 않는 확장자는 거부한다.

### 4.4 파일 모드

#### 4.4.1 통합 파일

필수 컬럼:

- `instrument_code`
- `observed_at`
- `price_value`

#### 4.4.2 종목별 파일

필수 컬럼:

- `observed_at`
- `price_value`

선택적으로 `instrument_code`가 있어도 되지만 값이 선택한 종목과 다르면 실패 처리한다.

### 4.5 허용 값 형식

#### 4.5.1 `observed_at`

허용 형식:

- `YYYY-MM-DD`
- ISO Instant 예: `2026-03-15T00:00:00Z`
- UTC LocalDateTime 파싱 가능 문자열 예: `2026-03-15T00:00:00`

#### 4.5.2 `price_value`

- `BigDecimal`로 파싱 가능한 숫자 문자열

### 4.6 권장 예시

```csv
instrument_code,observed_at,price_value
USD_KRW,2026-03-15T00:00:00Z,1450.12
XAU_USD,2026-03-15T00:00:00Z,3012.12
```

종목별 파일 예시:

```csv
observed_at,price_value
2026-03-15,1450.12
2026-03-16,1452.80
```

### 4.7 검증 규칙

- 비어 있는 CSV/XLSX 파일은 거부한다.
- 통합 파일에 `instrument_code`가 없으면 거부한다.
- `observed_at`, `price_value`가 없으면 거부한다.
- 지원하지 않는 `instrument_code`는 실패 처리한다.
- 날짜 형식이 잘못되면 실패 처리한다.
- 숫자 형식이 잘못되면 실패 처리한다.
- 종목별 파일 모드에서 row의 `instrument_code`가 선택 종목과 다르면 실패 처리한다.

### 4.8 저장 및 후처리

- 각 row는 `instrument_code + observed_at` 기준으로 upsert 저장한다.
- 공급자명은 `MANUAL_IMPORT`로 기록한다.
- 영향 종목 전체에 대해 `change_value`, `change_rate`를 재계산한다.
- 영향 종목의 장기 preset series 캐시를 삭제한다.

### 4.9 응답 필드

- `executedAt`
- `fileName`
- `selectedInstrument`
- `unifiedFile`
- `totalCount`
- `createdCount`
- `updatedCount`
- `skippedCount`
- `failedCount`
- `failures`

`failures` 원소 필드:

- `rowNumber`
- `message`

## 5. 백오피스 UI 기준

- 최신화 결과는 실행 시각, 생성/갱신/스킵 건수 카드로 보여준다.
- 임포트는 `통합 파일`, `종목별 파일` 모드를 전환할 수 있다.
- 파일 초기화 버튼을 제공한다.
- 실패 row는 상위 20건만 화면에 노출한다.

## 6. 운영 주의사항

- 공개 화면의 `새로고침` 버튼은 관리자 최신화 API를 호출하지 않는다.
- 최신화와 임포트 모두 완료 후 공개 series 캐시가 갱신되므로 장기 차트 정합성이 유지된다.
