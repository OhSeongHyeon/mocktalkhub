# CI/CD 개요

## 문서 상태

- 이 문서는 `2026-03-15` 기준 저장소의 실제 GitHub Actions workflow, Dockerfile, OCI 배포용 compose 파일을 기준으로 정리한 버전이다.

## 문서 목적

- 현재 `mocktalkback`, `mocktalkfront`의 CI/CD 구조를 한 문서에서 빠르게 파악할 수 있게 정리한다.
- PR 검증, 이미지 빌드, OCI 반영, 부가 운영 workflow를 구분해 본다.

## 대상 저장소

- 백엔드: `mocktalkback`
- 프론트엔드: `mocktalkfront`

## 현재 자동화 구성 한눈에 보기

## 1. PR 검증

- 백엔드
  - `mocktalkback/.github/workflows/backend-test.yml`
- 프론트
  - `mocktalkfront/.github/workflows/frontend-test.yml`

역할:

- `pull_request -> main` 기준 테스트/빌드 검증
- 운영 이미지 push 는 하지 않음

## 2. main 브랜치 이미지 빌드

- 백엔드
  - `mocktalkback/.github/workflows/build-backend-image.yml`
- 프론트
  - `mocktalkfront/.github/workflows/build-frontend-image.yml`

역할:

- `main` push 시 테스트 후 GHCR 이미지 빌드/푸시
- `prod-latest`, `sha-*` 태그 생성

## 3. OCI 배포

- 백엔드
  - `mocktalkback/.github/workflows/deploy-oci-backend.yml`
- 프론트
  - `mocktalkfront/.github/workflows/deploy-oci-frontend.yml`

역할:

- 빌드 workflow 성공 후 `workflow_run` 으로 자동 배포
- 필요 시 `workflow_dispatch` 수동 실행 가능

## 4. 부가 운영 workflow

- `mocktalkback/.github/workflows/keepalive.yml`

역할:

- Render healthcheck URL 을 10분 간격으로 호출
- OCI 배포 자체와는 별도 운영성 자동화

## 공통 CI/CD 흐름

1. PR 생성 시 test workflow 가 실행된다.
2. `main` 반영 시 image build workflow 가 실행된다.
3. GHCR 에 `prod-latest`, `sha-*` 이미지가 push 된다.
4. deploy workflow 가 OCI 서버에 SSH 접속한다.
5. OCI 서버에서 GHCR 로그인 후 `docker compose pull` 을 수행한다.
6. `docker compose up -d --no-build` 로 대상 서비스만 교체한다.
7. 내부 loopback health check 통과 시 배포 완료로 본다.

## 백엔드 CI/CD 흐름

## PR 검증 workflow

- 파일: `mocktalkback/.github/workflows/backend-test.yml`
- 트리거
  - `pull_request` to `main`
  - `workflow_dispatch`
- 주요 단계
  - checkout
  - JDK 21 설정
  - `./gradlew test`

## 이미지 빌드 workflow

- 파일: `mocktalkback/.github/workflows/build-backend-image.yml`
- 트리거
  - `main` push
  - `workflow_dispatch`
- 주요 단계
  - checkout
  - JDK 21 설정
  - `./gradlew test`
  - Docker Buildx 설정
  - GHCR 로그인
  - `ghcr.io/ohseonghyeon/mocktalkback:prod-latest`
  - `ghcr.io/ohseonghyeon/mocktalkback:sha-*`
  - amd64 이미지 push

메모:

- workflow 는 `github.actor + secrets.GITHUB_TOKEN` 조합으로 GHCR 에 로그인한다.
- Dockerfile 내부 빌드는 `./gradlew build -x test` 이지만, workflow 단계에서 이미 테스트를 선실행한다.

## OCI 배포 workflow

- 파일: `mocktalkback/.github/workflows/deploy-oci-backend.yml`
- 트리거
  - `Build Backend Image (GHCR)` 성공 후 `workflow_run`
  - `workflow_dispatch`
- 주요 단계
  - `OCI_SSH_KEY` 를 파일로 저장
  - `ssh-keyscan` 으로 `known_hosts` 등록
  - `ssh -i ~/.ssh/oci_deploy_key` 로 서버 접속
  - `docker login ghcr.io`
  - `docker network create mocktalk-internal || true`
  - `docker compose -f docker-compose.oci-deploy.yml pull backend`
  - pull 실패 시 진단 출력 후 1회 재시도
  - `docker compose -f docker-compose.oci-deploy.yml up -d --no-build backend`
  - `http://127.0.0.1:8082/api/health` 확인

## 프론트엔드 CI/CD 흐름

## PR 검증 workflow

- 파일: `mocktalkfront/.github/workflows/frontend-test.yml`
- 트리거
  - `pull_request` to `main`
  - `workflow_dispatch`
- 주요 단계
  - checkout
  - Node.js 22 설정
  - `npm ci`
  - `npm run test`
  - `npm run build`

## 이미지 빌드 workflow

- 파일: `mocktalkfront/.github/workflows/build-frontend-image.yml`
- 트리거
  - `main` push
  - `workflow_dispatch`
- 주요 단계
  - checkout
  - Node.js 22 설정
  - `npm ci`
  - `npm run test`
  - `npm run build`
  - Docker Buildx 설정
  - GHCR 로그인
  - `ghcr.io/ohseonghyeon/mocktalkfront:prod-latest`
  - `ghcr.io/ohseonghyeon/mocktalkfront:sha-*`
  - amd64 이미지 push

메모:

- workflow 에서 `npm ci/test/build` 를 먼저 수행한다.
- Dockerfile 내부에서도 `npm install`, `npm run format:check`, `npm run build` 가 다시 실행된다.

## OCI 배포 workflow

- 파일: `mocktalkfront/.github/workflows/deploy-oci-frontend.yml`
- 트리거
  - `Build Frontend Image (GHCR)` 성공 후 `workflow_run`
  - `workflow_dispatch`
- 주요 단계
  - `OCI_SSH_KEY` 를 파일로 저장
  - `ssh-keyscan` 으로 `known_hosts` 등록
  - `ssh -i ~/.ssh/oci_deploy_key` 로 서버 접속
  - `docker login ghcr.io`
  - `docker network create mocktalk-internal || true`
  - `docker compose -f docker-compose.oci-deploy.yml pull frontend`
  - pull 실패 시 진단 출력 후 1회 재시도
  - `docker compose -f docker-compose.oci-deploy.yml up -d --no-build frontend`
  - `http://127.0.0.1:$FRONTEND_PORT/` 확인

중요:

- `FRONTEND_OBJECT_STORAGE_BASE_URL` 시크릿이 비어 있으면 workflow 가 SSH 접속 전에 즉시 실패한다.

## GHCR 이미지 정책

- 백엔드
  - `ghcr.io/ohseonghyeon/mocktalkback:prod-latest`
  - `ghcr.io/ohseonghyeon/mocktalkback:sha-*`
- 프론트
  - `ghcr.io/ohseonghyeon/mocktalkfront:prod-latest`
  - `ghcr.io/ohseonghyeon/mocktalkfront:sha-*`

현재 OCI 배포는 digest pinning 이 아니라 `prod-latest` 기반 갱신이다.

## OCI 서버 반영 구조

## 백엔드

- compose 파일: `mocktalkback/docker-compose.oci-deploy.yml`
- 이미지: `BACKEND_IMAGE` 또는 기본 `prod-latest`
- 포트 바인딩
  - `127.0.0.1:8082:8082`
  - `127.0.0.1:8083:8083`
- env 파일
  - `./.env.prod`

## 프론트

- compose 파일: `mocktalkfront/docker-compose.oci-deploy.yml`
- 이미지: `FRONTEND_IMAGE` 또는 기본 `prod-latest`
- 포트 바인딩
  - `127.0.0.1:${FRONTEND_PORT:-8081}:80`
- env 파일
  - `./.env.production`
- 런타임 주입값
  - `PORT`
  - `BACKEND_BASE_URL`
  - `OBJECT_STORAGE_BASE_URL`

## 공통

- 내부 네트워크
  - `mocktalk-internal` 외부 네트워크 사용
- deploy workflow 는 네트워크가 없으면 `docker network create mocktalk-internal` 을 시도한다.
- 외부 공개는 loopback 바인딩 뒤 Nginx/Cloudflare Tunnel 경유를 전제로 한다.
- deploy workflow 는 원격 `.env` 파일을 업로드하지 않는다.

## 시크릿 정리

## 빌드 workflow

- 별도 GHCR 시크릿을 쓰지 않는다.
- `secrets.GITHUB_TOKEN` 으로 GHCR push 를 수행한다.

## deploy 공통 시크릿

- `OCI_HOST`
- `OCI_USER`
- `OCI_SSH_PORT`
- `OCI_SSH_KEY`
- `GHCR_USERNAME`
- `GHCR_TOKEN`

## 백엔드 deploy 추가 시크릿

- `OCI_DEPLOY_PATH`
  - 비어 있으면 기본 `~/mocktalkback`

## 프론트 deploy 추가 시크릿

- `OCI_FRONT_DEPLOY_PATH`
  - 비어 있으면 기본 `~/mocktalkfront`
- `FRONTEND_BACKEND_BASE_URL`
  - 비어 있으면 기본 `http://backend:8082`
- `FRONTEND_OBJECT_STORAGE_BASE_URL`
  - 현재 사실상 필수
- `FRONTEND_PORT`
  - 비어 있으면 기본 `8081`

## 로그와 진단 정보 위치

- GitHub Actions run 로그
  - `docker compose`, `curl`, `docker ps`, `docker logs`, 진단 함수 출력 포함
- `GITHUB_STEP_SUMMARY`
  - 성공 시 간단한 배포 완료 메시지 기록
- 서버 파일 로그
  - 현재 자동 저장되지 않음

## 현재 구조의 장점

- PR 검증과 운영 배포 경로가 분리돼 있다.
- 운영 서버에서 source build 없이 이미지 pull 기반 배포를 유지한다.
- pull 실패 시 진단과 재시도가 들어가 있다.
- SSH 접속이 action 의존이 아니라 키 파일 + `ssh -i` 방식으로 단순하다.

## 현재 구조의 주의점

- 원격 `.env.prod`, `.env.production` 파일 준비는 수동이다.
- OCI 서버의 `docker/containerd` 상태에 배포 성공 여부가 크게 좌우된다.
- 서버 로그 파일 저장은 아직 자동화되지 않았다.
- OCI 배포는 이전 digest 로 자동 rollback 하지 않는다.
