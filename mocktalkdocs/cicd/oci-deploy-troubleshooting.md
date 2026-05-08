# OCI 배포 트러블슈팅

## 문서 상태

- 이 문서는 `2026-03-15` 기준 현재 deploy workflow 와 compose 구성에 맞춰 정리한 버전이다.

## 문서 목적

- OCI 서버 배포 실패 시 원인 분류와 점검 순서를 정리한다.
- 실제 workflow 가 수행하는 단계 기준으로 어디서 실패했는지 빠르게 좁히는 데 목적이 있다.

## 대표 장애 유형

## 1. GHCR login / pull 실패

예시:

```text
failed commit on ref "layer-sha256:...": commit failed: rename ... no such file or directory
```

의미:

- 애플리케이션 코드 문제가 아니라 OCI 서버의 `docker/containerd` 이미지 저장 과정이 깨진 경우가 많다.

주요 원인 후보:

- 디스크 용량 부족
- inode 부족
- 이전 pull/prune 중단으로 인한 containerd 상태 꼬임
- Docker/containerd 런타임 일시 이상
- GHCR 인증 실패

## 2. compose up 실패

의미:

- 이미지는 pull 되었지만 컨테이너 재기동 단계에서 실패한 경우다.

주요 원인 후보:

- 원격 `.env.prod`, `.env.production` 누락
- `mocktalk-internal` 네트워크 문제
- 포트 충돌
- compose 환경변수 누락

## 3. backend health check 실패

확인 URL:

- `http://127.0.0.1:8082/api/health`

주요 원인 후보:

- 앱 설정값 누락
- DB/Redis 연결 실패
- 컨테이너 내부 예외

## 4. frontend health check 실패

확인 URL:

- `http://127.0.0.1:$FRONTEND_PORT/`

주요 원인 후보:

- Nginx 템플릿 렌더링 실패
- `OBJECT_STORAGE_BASE_URL` 또는 `BACKEND_BASE_URL` 값 문제
- 컨테이너 미기동
- 포트 바인딩 충돌

## 5. SSH / known_hosts 실패

의미:

- 배포 이전 단계에서 서버 연결 자체가 실패한 경우다.

주요 원인 후보:

- `OCI_HOST`, `OCI_USER`, `OCI_SSH_PORT`, `OCI_SSH_KEY` 오류
- 서버 방화벽 또는 네트워크 이슈

## 6. 프론트 시크릿 사전 검증 실패

예시:

```text
FRONTEND_OBJECT_STORAGE_BASE_URL secret is required.
```

의미:

- SSH 접속 이전에 workflow 가 입력값 검증에서 멈춘 경우다.

주요 원인 후보:

- `FRONTEND_OBJECT_STORAGE_BASE_URL` 시크릿 미설정
- 시크릿 값 비움

## 1차 점검 명령

서버에서 먼저 확인:

```bash
df -h
df -i
docker system df
docker ps
docker ps -a
docker network ls
```

필요 시 배포 경로에서 추가 확인:

```bash
cd ~/mocktalkback
docker compose -f docker-compose.oci-deploy.yml ps

cd ~/mocktalkfront
docker compose -f docker-compose.oci-deploy.yml ps
```

확인 포인트:

- 디스크 여유 공간
- inode 여유
- Docker 이미지/컨테이너 사용량
- 대상 컨테이너 상태
- `mocktalk-internal` 네트워크 존재 여부

## GHCR pull 실패 시 복구 절차

## 1. 불필요한 리소스 정리

```bash
docker image prune -af
docker container prune -f
docker network prune -f
```

## 2. Docker 재시작

```bash
sudo systemctl restart docker
```

## 3. GHCR 로그인 확인

```bash
docker login ghcr.io
```

## 4. 내부 네트워크 확인

```bash
docker network create mocktalk-internal >/dev/null 2>&1 || true
```

## 5. 수동 pull 재시도

백엔드:

```bash
docker pull ghcr.io/ohseonghyeon/mocktalkback:prod-latest
```

프론트:

```bash
docker pull ghcr.io/ohseonghyeon/mocktalkfront:prod-latest
```

## 6. 수동 compose up

백엔드:

```bash
cd ~/mocktalkback
docker compose -f docker-compose.oci-deploy.yml up -d --no-build backend
```

프론트:

```bash
cd ~/mocktalkfront
export FRONTEND_IMAGE=ghcr.io/ohseonghyeon/mocktalkfront:prod-latest
export BACKEND_BASE_URL=http://backend:8082
export OBJECT_STORAGE_BASE_URL=https://your-object-storage.example
export FRONTEND_PORT=8081
docker compose -f docker-compose.oci-deploy.yml up -d --no-build frontend
```

## 7. 최종 확인

```bash
docker ps
curl -i http://127.0.0.1:8082/api/health
curl -I http://127.0.0.1:8081/
```

## env 파일 누락 의심 시 확인

백엔드:

```bash
cd ~/mocktalkback
ls -l .env.prod
```

프론트:

```bash
cd ~/mocktalkfront
ls -l .env.production
```

메모:

- deploy workflow 는 env 파일을 서버에 복사하지 않는다.
- 이 파일들이 없으면 compose 단계에서 실패할 수 있다.

## backend health 실패 시 확인

```bash
docker logs --tail 200 mocktalk-back
curl -i http://127.0.0.1:8082/api/health
```

주요 확인 포인트:

- DB 접속 오류
- Redis 접속 오류
- Spring Boot 시작 실패
- 포트 바인딩 문제

## frontend health 실패 시 확인

```bash
docker logs --tail 200 mocktalk-front
curl -I http://127.0.0.1:8081/
```

주요 확인 포인트:

- Nginx 설정 렌더링 실패
- `OBJECT_STORAGE_BASE_URL` 값 문제
- `BACKEND_BASE_URL` 값 문제
- 컨테이너 내부 포트와 외부 바인딩 불일치

## 이번 실제 사례 정리

## 증상

- GitHub Actions deploy 단계에서 `docker compose pull backend` 실패
- 에러:
  - `failed commit on ref "layer-sha256:..."`
  - `rename ... no such file or directory`

## 확인 결과

- 디스크 여유 충분
- inode 여유 충분
- 수동 `docker pull` 성공
- 수동 `docker compose up -d --no-build backend` 성공
- 운영 컨테이너 정상 기동

## 결론

- 코드나 이미지 자체 문제보다 OCI 서버의 `docker/containerd` pull 과정에서 일시적으로 발생한 런타임 문제로 보는 것이 타당하다.

## 로그 확인 위치

## 기본 위치

- GitHub Actions run 로그

## step summary

- 배포 완료 같은 짧은 결과만 남음

## 서버 파일 로그

- 현재 자동 저장되지 않음
- 필요 시 `tee` 로 별도 저장해야 함

예시:

```bash
mkdir -p ~/deploy-logs
docker compose -f docker-compose.oci-deploy.yml pull backend 2>&1 | tee -a ~/deploy-logs/backend-deploy-$(date +%F).log
```

## 주의 메모

- `/var/lib/containerd/...` 경로는 일반 사용자로 접근하면 `Permission denied` 가 날 수 있다.
- 이 자체는 이상 증상이 아니다.
- 실제 내용 확인이 필요하면 `sudo` 권한으로 봐야 한다.
