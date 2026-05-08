# 콘텐츠 시세 백필 데이터셋 포맷

## 목표

- 백오피스의 `통합 파일 임포트`, `종목별 파일 임포트`를 모두 지원합니다.
- 필수 컬럼만 사용해 운영자가 파일을 다루기 쉽게 유지합니다.

## 통합 파일

백오피스에서 종목을 별도로 선택하지 않고 한 번에 임포트할 때 사용합니다.

### 컬럼

- `instrument_code`
- `observed_at`
- `price_value`

### 예시

```csv
instrument_code,observed_at,price_value
USD_KRW,2026-03-13,1450.12000000
EUR_KRW,2026-03-13,1581.43000000
XAU_USD,2026-03-13,2987.70000000
```

## 종목별 파일

백오피스에서 종목을 직접 선택한 뒤 임포트할 때 사용합니다.

### 컬럼

- `observed_at`
- `price_value`

### 예시

```csv
observed_at,price_value
2026-03-13,1450.12000000
2026-03-14,1448.55000000
```

## observed_at 규칙

- 권장 형식: `YYYY-MM-DD`
- 임포트 서비스는 `YYYY-MM-DD`, `ISO-8601 UTC`, `UTC 기준 LocalDateTime`을 허용하지만
  데이터셋은 일관성을 위해 날짜 형식만 사용합니다.

## instrument_code 허용값

- `USD_KRW`
- `EUR_KRW`
- `JPY_KRW`
- `XAU_USD`
- `XAU_KRW`

## 정렬 규칙

- 통합 파일: `observed_at ASC`, 같은 날짜 내에서는 종목 코드 순
- 종목별 파일: `observed_at ASC`

## 파생 규칙

- `XAU_KRW`는 외부 원시 소스가 아니라 파생 값입니다.
- 같은 날짜의 `XAU_USD`에 대해 가장 가까운 직전 `USD_KRW`를 곱해 계산합니다.

## DB 직접 임포트 파일

`DBeaver`, `Supabase` 같은 도구로 `tb_market_snapshots`에 바로 넣을 때 사용합니다.

### 컬럼

- `instrument_code`
- `market_group`
- `provider_name`
- `base_currency`
- `quote_currency`
- `price_value`
- `change_value`
- `change_rate`
- `observed_at`

### 예시

```csv
instrument_code,market_group,provider_name,base_currency,quote_currency,price_value,change_value,change_rate,observed_at
USD_KRW,FX,BACKFILL_FRANKFURTER,USD,KRW,1194.35000000,,,2016-03-15T00:00:00Z
EUR_KRW,FX,BACKFILL_FRANKFURTER,EUR,KRW,1326.80000000,,,2016-03-15T00:00:00Z
USD_KRW,FX,BACKFILL_FRANKFURTER,USD,KRW,1194.85000000,0.50000000,0.041864,2016-03-16T00:00:00Z
```

### provider_name 규칙

- `USD_KRW`, `EUR_KRW`, `JPY_KRW`: `BACKFILL_FRANKFURTER`
- `XAU_USD`: `BACKFILL_YAHOO_FINANCE`
- `XAU_KRW`: `BACKFILL_DERIVED`

### change 계산 규칙

- 같은 `instrument_code` 내에서 직전 row와 비교합니다.
- 첫 row는 `change_value`, `change_rate`를 비워 둡니다.
- `change_rate = ((현재값 - 직전값) / 직전값) * 100`
