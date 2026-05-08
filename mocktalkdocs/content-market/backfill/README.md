# 콘텐츠 시세 백필 데이터셋

이 폴더는 `콘텐츠 > 환율 / 금 시세` 기능의 과거 데이터 백필용 CSV 데이터셋과 생성 기준을 정리합니다.

## 목적

- 운영자가 `CSV / XLSX 임포트`로 과거 시세를 채울 수 있게 합니다.
- 외부 API 히스토리 제약에 덜 묶이도록, 일회성 데이터셋을 먼저 확보합니다.
- 앱의 임포트 포맷과 동일한 컬럼 구조를 유지합니다.

## 구성

- `dataset-spec.md`
  - 통합 파일 / 종목별 파일 / DB 직접 임포트 파일 포맷 정의
- `datasets/`
  - 실제 백필용 CSV 결과물
- `datasets/generation-summary.md`
  - 생성 범위와 종목별 row 수 요약

## 생성 전략

- 환율
  - 소스: Frankfurter
  - 대상: `USD_KRW`, `EUR_KRW`, `JPY_KRW`
- 금 시세
  - 소스: Yahoo Finance `GC=F`
  - 대상: `XAU_USD`
- 파생 값
  - `XAU_KRW = XAU_USD * 가장 가까운 직전 USD_KRW`

## 생성 스크립트

버전관리 대상 스크립트는 아래 경로에 있습니다.

- [content_market_backfill_dataset.py](/D:/MyProject/mocktalk-workspace/mocktalkback/scripts/content_market_backfill_dataset.py)

예시:

```powershell
python mocktalkback/scripts/content_market_backfill_dataset.py `
  --start-date 2016-03-15 `
  --end-date 2026-03-15
```

## 참고

- 통합 파일은 `instrument_code, observed_at, price_value`
- 종목별 파일은 `observed_at, price_value`
- DB 직접 임포트 파일은 `created_at`, `updated_at`를 제외한 직접 입력 대상 컬럼을 포함합니다.
- `created_at`, `updated_at`는 DB 기본값으로 채워집니다.
- `observed_at`는 `YYYY-MM-DD` 형식으로 저장합니다.
