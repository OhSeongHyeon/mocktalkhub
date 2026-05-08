# OCI 배포 워크플로우

## 문서 상태

- 이 문서는 `2026-03-15` 기준 실제 workflow 와 compose 설정을 기준으로 정리했다.

## 문서 목적

- 백엔드/프론트의 OCI 배포 절차를 실제 workflow 기준으로 설명한다.
- 자동 배포와 수동 복구 배포가 어떤 순서로 동작하는지 정리한다.

## 전제 조건

- OCI 서버에 Docker / Docker Compose plugin 이 설치되어 있어야 한다.
- 백엔드 배포 경로에는 `docker-compose.oci-deploy.yml`, `.env.prod` 가 있어야 한다.
- 프론트 배포 경로에는 `docker-compose.oci-deploy.yml`, `.env.production` 이 있어야 한다.
- `mocktalk-internal` 네트워크가 없더라도 deploy workflow 가 생성 시도를 한다.
- 외부 공개는 loopback 바인딩 뒤 Nginx / Cloudflare Tunnel 이 담당한다.

## 자동 배포 흐름

## 1. PR 검증

- 백엔드
  - `backend-test.yml`
- 프론트
  - `frontend-test.yml`

역할:

- `pull_request -> main` 기준 테스트/빌드 검증
- OCI 배포는 하지 않음

## 2. main 반영 후 이미지 빌드

- 백엔드
  - `build-backend-image.yml`
- 프론트
  - `build-frontend-image.yml`

공통적으로 수행하는 것:

- 소스 checkout
- 런타임 설정
  - 백엔드: JDK 21
  - 프론트: Node.js 22
- 테스트 실행
- 이미지 buildx 빌드
- GHCR `prod-latest`, `sha-*` push

## 3. deploy workflow 트리거

- 백엔드
  - `deploy-oci-backend.yml`
- 프론트
  - `deploy-oci-frontend.yml`

트리거 조건:

- 대응 build workflow 가 `success`
- 또는 `workflow_dispatch`

## 4. SSH 접속 준비

현재 workflow 는 `ssh-agent` 를 쓰지 않고 아래 순서로 동작한다.

- `OCI_SSH_KEY` 를 `~/.ssh/oci_deploy_key` 파일로 저장
- `chmod 600`
- `ssh-keyscan` 으로 `known_hosts` 등록
- 이후 `ssh -i ~/.ssh/oci_deploy_key -o IdentitiesOnly=yes ...` 로 접속

## 5. OCI 서버에서 배포 준비

원격 서버 공통 준비 단계:

- 배포 경로로 이동
- 이미지 태그 환경변수 export
- `docker login ghcr.io`
- `docker network create mocktalk-internal >/dev/null 2>&1 || true`

프론트는 추가로 아래 값을 export 한다.

- `BACKEND_BASE_URL`
- `OBJECT_STORAGE_BASE_URL`
- `FRONTEND_PORT`

## 6. 이미지 pull

공통 구조:

- `docker compose -f docker-compose.oci-deploy.yml pull <service>`
- 실패 시 진단 함수 실행
  - `df -h`
  - `df -i`
  - `docker system df`
  - `docker ps -a`
  - `docker images --digests`
- `docker image prune -af`
- Docker daemon 재시작 시도
- GHCR 재로그인
- pull 1회 재시도

서비스별 명령:

- 백엔드
  - `docker compose -f docker-compose.oci-deploy.yml pull backend`
- 프론트
  - `docker compose -f docker-compose.oci-deploy.yml pull frontend`

## 7. 컨테이너 재기동

서비스별 명령:

- 백엔드
  - `docker compose -f docker-compose.oci-deploy.yml up -d --no-build backend`
- 프론트
  - `docker compose -f docker-compose.oci-deploy.yml up -d --no-build frontend`

실패 시 공통 진단:

- 진단 함수 출력
- `docker compose ps`
- 대상 컨테이너 `docker logs --tail 200`

## 8. health check

## 백엔드

- 확인 URL
  - `http://127.0.0.1:8082/api/health`
- 재시도
  - 최대 150회
  - 2초 간격

## 프론트

- 확인 URL
  - `http://127.0.0.1:$FRONTEND_PORT/`
- 재시도
  - 최대 60회
  - 2초 간격

실패 시:

- 진단 함수 출력
- `docker compose ps`
- `docker ps`
- 대상 컨테이너 로그 출력

## 9. 성공 후 정리

- `docker image prune -f`
- `GITHUB_STEP_SUMMARY` 에 완료 메시지 기록

## 수동 배포 절차

자동 배포가 실패했을 때는 서버에서 아래 순서로 복구 가능하다.

## 백엔드

```bash
docker login ghcr.io
docker network create mocktalk-internal >/dev/null 2>&1 || true
docker pull ghcr.io/ohseonghyeon/mocktalkback:prod-latest
cd ~/mocktalkback
docker compose -f docker-compose.oci-deploy.yml up -d --no-build backend
curl -i http://127.0.0.1:8082/api/health
```

## 프론트

```bash
docker login ghcr.io
docker network create mocktalk-internal >/dev/null 2>&1 || true
cd ~/mocktalkfront
export FRONTEND_IMAGE=ghcr.io/ohseonghyeon/mocktalkfront:prod-latest
export BACKEND_BASE_URL=http://backend:8082
export OBJECT_STORAGE_BASE_URL=https://your-object-storage.example
export FRONTEND_PORT=8081
docker pull ghcr.io/ohseonghyeon/mocktalkfront:prod-latest
docker compose -f docker-compose.oci-deploy.yml up -d --no-build frontend
curl -I http://127.0.0.1:8081/
```

주의:

- 프론트는 `OBJECT_STORAGE_BASE_URL` 이 비어 있으면 현재 배포 workflow 기준으로 실패 처리한다.

## 배포 성공 확인 포인트

## 서버 측

- `docker ps`
- `docker compose -f docker-compose.oci-deploy.yml ps`
- health endpoint 응답
- 컨테이너 재기동 시각

## GitHub Actions 측

- build workflow 성공
- deploy workflow 성공
- step summary 의 배포 완료 메시지

## 현재 배포 방식의 특징

## 장점

- source build 없이 GHCR pull 기반이라 서버 작업이 단순하다.
- pull 실패 시 진단과 재시도가 들어가 있다.
- SSH 접속 구조가 단순해 action 런타임 이슈 영향을 줄였다.

## 한계

- 원격 env 파일 관리가 수동이다.
- 서버 로그 파일 보존은 아직 별도 없다.
- rollback 은 자동화되어 있지 않다.
