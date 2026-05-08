# 생성 요약

- 생성 범위: `2016-03-15 ~ 2026-03-15`
- 통합 파일: `instrument_code, observed_at, price_value`
- 종목별 파일: `observed_at, price_value`

## 종목별 row 수

- 통합 백오피스 CSV row 수: 12706
- DB 직접 임포트 CSV row 수: 12706

- `USD_KRW`: 2560
- `EUR_KRW`: 2560
- `JPY_KRW`: 2560
- `XAU_USD`: 2513
- `XAU_KRW`: 2513

## 파생 규칙

- `XAU_KRW`는 같은 날짜의 `XAU_USD`에 대해 가장 가까운 직전 `USD_KRW`를 곱해 계산합니다.
