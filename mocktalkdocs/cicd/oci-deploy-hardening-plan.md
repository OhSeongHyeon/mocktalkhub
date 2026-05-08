# OCI 배포 Hardening 계획

## 문서 상태

- 이 문서는 `2026-03-15` 기준 현재 deploy workflow 에 이미 반영된 항목과 남은 개선 과제를 분리해 정리한 버전이다.

## 문서 목적

- 백엔드/프론트 OCI 배포 워크플로우를 더 안정적으로 만들기 위한 개선 항목을 정리한다.
- 실제로 반영된 hardening 과 아직 남은 hardening 을 구분한다.

## 적용 대상

- `mocktalkback/.github/workflows/deploy-oci-backend.yml`
- `mocktalkfront/.github/workflows/deploy-oci-frontend.yml`

두 workflow 모두 `SSH -> docker login -> docker compose pull -> docker compose up -> health check` 구조가 같다.

## 현재 목표

- 외부 런타임 장애가 배포 전체 실패로 이어질 때 진단 가능성을 높인다.
- 일시적 pull 실패를 자동 재시도로 흡수한다.
- 배포 실패 시 Actions 로그만으로 1차 원인 분류가 가능하게 한다.

## 이미 적용된 항목

## 1. pull 실패 시 진단 로그 강화

현재 출력 항목:

- `df -h`
- `df -i`
- `docker system df`
- `docker ps -a`
- `docker images --digests`

## 2. pull 1회 재시도

- 초기 pull 실패 후
  - `docker image prune -af`
  - Docker daemon 재시작 시도
  - GHCR 재로그인
  - 네트워크 생성 재시도
  - pull 재실행

## 3. up / health 실패 시 컨테이너 상태 출력

출력 항목:

- `docker compose ps`
- `docker ps`
- 대상 컨테이너 `docker logs --tail 200`

## 4. SSH 접속 방식 단순화

- `webfactory/ssh-agent` 의존 제거
- 현재는 키 파일을 만들고 `ssh -i` 로 직접 접속

## 5. 배포 충돌 방지

- 백엔드/프론트 deploy workflow 에 각각 concurrency group 설정

## 6. 네트워크 생성 보강

- `mocktalk-internal` 네트워크가 없을 때 자동 생성 시도

## 현재 남아 있는 개선 항목

## 1. 서버 로그 파일 저장

현재 상태:

- 서버 파일 로그 자동 저장 없음
- 진단 정보는 대부분 Actions 로그에만 남는다

개선안:

```bash
mkdir -p ~/deploy-logs
docker compose -f docker-compose.oci-deploy.yml pull backend 2>&1 | tee -a ~/deploy-logs/backend-deploy-$(date +%F).log
```

기대 효과:

- 동일 서버에서 반복되는 장애 패턴 추적이 쉬워진다.

## 2. rollback 기준 정리

현재 상태:

- 배포는 `prod-latest` 기준 갱신
- 이전 digest 로 자동 rollback 하지 않음

개선안:

- 최근 배포 성공 digest 를 summary 또는 서버 파일로 남기기
- 수동 rollback 절차를 별도 문서화하기

## 3. env 파일 준비 상태 검증

현재 상태:

- deploy workflow 는 `.env.prod`, `.env.production` 존재 여부를 따로 검사하지 않는다.
- 없으면 compose 단계에서 실패한다.

개선안:

- 원격 접속 직후 `test -f` 로 필수 env 파일 존재 여부를 먼저 확인
- 누락 시 더 명확한 에러 메시지로 즉시 종료

## 4. 프론트 시크릿 검증 확장

현재 상태:

- `FRONTEND_OBJECT_STORAGE_BASE_URL` 만 명시적으로 비어 있으면 실패 처리한다.

개선안:

- 필요하면 `OCI_FRONT_DEPLOY_PATH`, `FRONTEND_PORT`, `FRONTEND_BACKEND_BASE_URL` 의 최종값도 summary 에 남기기

## 5. 진단 로그 세분화

추가 후보:

- `docker version`
- `docker info`
- 실패 단계 이름
- 서비스명
- 재시도 횟수

## 6. 다른 workflow 의 런타임 경고 점검

현재 상태:

- deploy workflow 에서 `webfactory/ssh-agent` 제거 완료

남은 확인:

- 다른 workflow 에 Node 구버전 action 이 남아 있는지 주기적으로 점검

## 운영상 주의 메모

- `docker image prune -af` 는 공격적인 정리라 pull 장애 복구에는 유효하지만, 서버 전체 이미지 캐시를 크게 지울 수 있다.
- OCI free tier 환경에서는 디스크 여유 확보에 도움되지만, 사용 중인 다른 이미지/서비스가 있다면 영향도를 같이 봐야 한다.

## 권장 구현 순서

1. 원격 env 파일 존재 여부 사전 검증 추가
2. 서버 로그 파일 저장 여부 결정
3. rollback 기준 문서화
4. 진단 로그 세분화
5. 다른 workflow 런타임 점검

## 완료 기준

- 백엔드와 프론트 모두 동일 수준의 hardening 이 적용된다.
- pull 실패 시 Actions 로그만으로 1차 원인 분류가 가능하다.
- env 파일 누락과 런타임 장애를 구분해 보여줄 수 있다.
- rollback 판단에 필요한 최소 이력이 남는다.
