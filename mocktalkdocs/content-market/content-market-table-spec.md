# 콘텐츠 / 환율·금 시세 테이블 정의서

## 문서 목적

- `환율/금 시세` 기능에서 사용하는 시세 스냅샷 테이블의 실제 스키마를 정리한다.
- 현재 Flyway 마이그레이션과 엔티티 설계를 기준으로 제약조건과 인덱스를 명시한다.
- 공개 조회 API와 운영 임포트가 어떤 키로 적재되는지 문서화한다.

## 1. 설계 원칙

- 시세 그래프는 외부 히스토리가 아니라 내부 스냅샷 데이터를 기준으로 만든다.
- 환율과 금 시세를 별도 테이블로 분리하지 않고 공통 스냅샷 테이블 1개로 관리한다.
- 종목 식별은 `instrument_code`로 통일한다.
- 데이터 기준 시각은 `observed_at`, 저장/갱신 시각은 `created_at`, `updated_at`으로 분리한다.
- 중복 기준은 `instrument_code + observed_at`이다.

## 2. 테이블 개요

### 2.1 테이블명

- `tb_market_snapshots`

### 2.2 용도

- 종목별 최신 스냅샷 저장
- overview API 최신값 조회
- series API 기간별 시계열 조회
- 운영 임포트와 자동 수집의 공통 적재 대상

## 3. 실제 컬럼 정의

| 컬럼명 | 타입 | NULL | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `market_snapshot_id` | `BIGINT` | N | Identity | 시세 스냅샷 PK |
| `instrument_code` | `VARCHAR(32)` | N |  | 종목 코드 |
| `market_group` | `VARCHAR(16)` | N |  | 시세 그룹, 예: `FX`, `METAL` |
| `provider_name` | `VARCHAR(32)` | N |  | 데이터 공급자 이름 |
| `base_currency` | `VARCHAR(16)` | N |  | 기준 통화 또는 자산 코드 |
| `quote_currency` | `VARCHAR(16)` | N |  | 비교 통화 |
| `price_value` | `NUMERIC(20,8)` | N |  | 시세 값 |
| `change_value` | `NUMERIC(20,8)` | Y |  | 직전 저장값 대비 변화량 |
| `change_rate` | `NUMERIC(12,6)` | Y |  | 직전 저장값 대비 변화율(%) |
| `observed_at` | `TIMESTAMPTZ` | N |  | 외부 공급자 기준 시각 |
| `created_at` | `TIMESTAMPTZ` | N | `now()` | 내부 저장 시각 |
| `updated_at` | `TIMESTAMPTZ` | N | `now()` | 내부 수정 시각 |

지원 종목:

- `USD_KRW`
- `EUR_KRW`
- `JPY_KRW`
- `XAU_USD`
- `XAU_KRW`

## 4. 컬럼 설명

### 4.1 `instrument_code`

- API 파라미터, 조회 조건, 프론트 표시 종목 식별에 공통으로 사용한다.

### 4.2 `provider_name`

- 현재값 수집 시 공급자, 수동 임포트 여부, 파생값 여부를 식별한다.
- 예시:
  - Yahoo Finance 계열 공급자명
  - `DERIVED_YAHOO_FINANCE`
  - `MANUAL_IMPORT`

### 4.3 `change_value`, `change_rate`

- 저장 시점에 직전 스냅샷과 비교해 계산한다.
- 임포트 후에는 영향 종목 전체를 다시 순회하며 재계산한다.

### 4.4 `observed_at`

- 실제 그래프 시간축 기준 컬럼이다.
- 공개 `series` API는 이 값을 기준으로 오름차순 조회한다.

### 4.5 `updated_at`

- 같은 `instrument_code + observed_at` 키가 다시 들어와 row가 갱신될 때 변경된다.

## 5. 실제 제약조건

### 5.1 PK

- `PRIMARY KEY (market_snapshot_id)`

### 5.2 UNIQUE

- `uq_tb_market_snapshots_instrument_code_observed_at`
  - `(instrument_code, observed_at)`

`provider_name`은 UNIQUE 구성에 포함되지 않는다. 같은 종목, 같은 시각의 값이 다시 들어오면 기존 row를 갱신하는 구조다.

### 5.3 CHECK

- 현재 `V14__content_market_snapshots.sql`에는 별도 CHECK 제약조건이 없다.
- 값 검증은 애플리케이션 로직과 enum 매핑으로 보완한다.

## 6. 실제 인덱스

### 6.1 핵심 조회 인덱스

- `ix_tb_market_snapshots_instrument_code_observed_at`
  - `(instrument_code, observed_at DESC)`

용도:

- 특정 종목의 최신값 조회
- 특정 종목의 기간별 시계열 조회

### 6.2 보조 인덱스

- `ix_tb_market_snapshots_market_group_observed_at`
  - `(market_group, observed_at DESC)`

용도:

- 운영 점검
- 그룹 단위 확장 조회 대비

## 7. 실제 DDL

```sql
CREATE TABLE tb_market_snapshots
(
  market_snapshot_id BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY,
  instrument_code    VARCHAR(32)   NOT NULL,
  market_group       VARCHAR(16)   NOT NULL,
  provider_name      VARCHAR(32)   NOT NULL,
  base_currency      VARCHAR(16)   NOT NULL,
  quote_currency     VARCHAR(16)   NOT NULL,
  price_value        NUMERIC(20,8) NOT NULL,
  change_value       NUMERIC(20,8),
  change_rate        NUMERIC(12,6),
  observed_at        TIMESTAMPTZ   NOT NULL,
  created_at         TIMESTAMPTZ   NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ   NOT NULL DEFAULT now(),
  PRIMARY KEY (market_snapshot_id)
);

ALTER TABLE tb_market_snapshots
  ADD CONSTRAINT uq_tb_market_snapshots_instrument_code_observed_at
    UNIQUE (instrument_code, observed_at);

CREATE INDEX IF NOT EXISTS ix_tb_market_snapshots_instrument_code_observed_at
  ON tb_market_snapshots (instrument_code, observed_at DESC);

CREATE INDEX IF NOT EXISTS ix_tb_market_snapshots_market_group_observed_at
  ON tb_market_snapshots (market_group, observed_at DESC);
```

## 8. 조회 패턴

### 8.1 overview API

- 종목별 최신 1건 조회
- 필요 시 직전 1건을 추가로 조회해 `change_value`, `change_rate`를 계산한다.

### 8.2 series API

- 조건: `instrument_code + observed_at 범위`
- 정렬: `observed_at ASC`
- 기간:
  - `TEN_YEAR`
  - `FIVE_YEAR`
  - `THREE_YEAR`
  - `YEAR`
  - `HALF_YEAR`
  - `QUARTER`
  - `MONTH`
  - `WEEK`
  - `CUSTOM`

## 9. 저장 및 갱신 규칙

- 자동 수집과 관리자 최신화는 동일한 upsert 로직을 사용한다.
- 임포트도 동일한 upsert 키를 사용하되 공급자명을 `MANUAL_IMPORT`로 기록한다.
- 동일 키에 값, 변동값, 변동률, 공급자명이 모두 같으면 `SKIPPED` 처리한다.
- 동일 키에 차이가 있으면 기존 row를 `UPDATED` 처리한다.

## 10. 보관 정책

- 현재는 삭제 배치 없이 장기 보관 전제로 운영한다.
- 배포 시점부터 적재된 일간 스냅샷을 그대로 유지한다.
- 과거 데이터가 필요하면 운영 임포트나 백필 CSV를 사용한다.

## 11. 후속 확장 후보

- 원문 payload 저장 컬럼 추가
- 장기 보관용 집계 테이블 분리
- 다중 공급자 우선순위 정책 추가
- 데이터 보정 여부 표시 컬럼 추가
