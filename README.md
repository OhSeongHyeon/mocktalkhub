# Mocktalk Hub (로컬 개발 스택 실행 허브)

이 저장소는 **Mocktalk 프론트/백엔드 + 인프라 컨테이너**를 한 번에 실행하기 위한 허브입니다.

포함 대상:
- Frontend (`frontend`)
- Backend (`backend`)
- PostgreSQL
- Redis
- MinIO
- Prometheus
- Grafana

## 1. 사전 준비

필수:
- Docker Desktop (또는 Docker Engine + Docker Compose)
- Python 3.8+
- Git

## 2. 빠른 시작

### Windows

실행:
```bat
start-dev.bat
```

중지:
```bat
stop-dev.bat
```

참고:
- 기본적으로 실행 후 창이 유지됩니다.
- 창 자동 닫힘이 필요하면:
```bat
set NO_PAUSE=1 && start-dev.bat
```

### Linux / macOS

실행:
```bash
./start-dev.sh
```

중지:
```bash
./stop-dev.sh
```

## 3. 1분 초기 세팅 체크리스트

1. Docker 동작 확인
```bash
docker compose version
```

2. Python 동작 확인
```bat
py -3 --version
```
```bash
python3 --version
```

3. 개발 스택 실행
```bat
start-dev.bat
```
```bash
./start-dev.sh
```

4. 접속 확인
- Frontend: `http://localhost:8081`
- Backend API: `http://localhost:8082`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- MinIO Console: `http://localhost:9001`

## 4. 자주 쓰는 명령 치트시트

```bash
# 저장소 최신화 후 전체 기동
python3 devctl.py up --pull

# 전체 기동 후 브라우저 자동 열기
python3 devctl.py up --open

# 실시간 백엔드 로그 보기
python3 devctl.py logs -f backend

# 전체 재시작 + 최신화 + 브라우저 열기
python3 devctl.py restart --pull --open

# 전체 중지 (데이터 볼륨 유지)
python3 devctl.py down

# 전체 중지 + 볼륨까지 삭제(주의: DB/Redis/MinIO 데이터 삭제)
python3 devctl.py down --volumes
```

## 5. devctl CLI 사용법

기본 도움말:
```bash
python3 devctl.py --help
```

주요 명령:
- `up`: 전체 스택 실행
- `down`: 전체 스택 중지/정리
- `restart`: 전체 스택 재시작
- `status`: 컨테이너 상태 확인
- `logs`: 로그 확인

옵션 요약:
- `up --pull`: 실행 전 `backend`, `frontend`에 `git pull --ff-only`
- `up --open`: 실행 완료 후 프론트 주소를 브라우저로 열기
- `up --foreground`: 포그라운드 실행
- `up --no-build`: 이미지 빌드 생략
- `down --volumes`: 볼륨까지 삭제
- `restart --pull`: 재시작 전 `git pull --ff-only`
- `restart --open`: 재시작 완료 후 브라우저 열기

예시:
```bash
python3 devctl.py up --pull
python3 devctl.py up --open
python3 devctl.py restart --pull --open
python3 devctl.py logs -f backend
python3 devctl.py down
```

## 6. 자동 저장소 준비 동작

`devctl.py`는 실행 시 아래를 자동 확인합니다.

- `backend` 또는 `frontend` 디렉토리가 없으면 자동 `git clone`
- 디렉토리는 있는데 필수 파일이 없으면 오류로 중단
- `--pull` 옵션 사용 시 기존 저장소 최신화

원격 저장소:
- Frontend: `https://github.com/OhSeongHyeon/mocktalkfront.git`
- Backend: `https://github.com/OhSeongHyeon/mocktalkback.git`

## 7. 기본 접속 주소

`.env.dev` 기본값 기준:
- Frontend: `http://localhost:8081`
- Backend API: `http://localhost:8082`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- MinIO Console: `http://localhost:9001`

`up`/`restart` 성공 후 `devctl.py`가 위 주소를 콘솔에 출력합니다.

## 8. 환경 변수

실행 설정은 루트의 `.env.dev`를 사용합니다.

자주 수정하는 항목:
- `FRONTEND_HOST_PORT`
- `SERVER_PORT`
- `PROMETHEUS_PORT`
- `GRAFANA_PORT`
- `MINIO_CONSOLE_PORT`

포트를 변경하면 출력되는 접속 주소도 변경 값 기준으로 안내됩니다.

## 9. 트러블슈팅

### Docker 오류

메시지 예시:
- `Docker is not available. Check whether Docker Desktop is running.`

조치:
- Docker Desktop 실행 상태 확인
- `docker compose version` 명령이 동작하는지 확인

### Python 오류

메시지 예시:
- `Python 3 is not installed. Install Python 3 and run again.`

조치:
- Python 3 설치 후 다시 실행
- Windows에서 `py -3 --version` 확인

### devctl.py 파일 찾기 오류

메시지 예시:
- `devctl.py was not found: ...`

조치:
- `start-dev.*`, `stop-dev.*`, `devctl.py`가 같은 디렉토리에 있는지 확인

## 10. Windows에서 .sh 테스트 방법 (WSL/Git Bash)

Windows에서도 `.sh` 런처를 테스트할 수 있습니다.

### WSL에서 테스트

```bash
wsl
cd /mnt/c/project-workspace/mocktalkhub
bash -n start-dev.sh stop-dev.sh
./start-dev.sh
```

권장 순서:
1. `bash -n ...`으로 문법 검사
2. `./start-dev.sh`로 실제 실행 테스트

### Git Bash에서 테스트

```bash
cd /c/project-workspace/mocktalkhub
bash -n start-dev.sh stop-dev.sh
./start-dev.sh
```

### 자주 나오는 이슈

- `permission denied`가 나오면:
```bash
bash start-dev.sh
```

- `bash\r` 또는 줄바꿈 관련 에러가 나오면:
  - 파일 줄바꿈을 `LF`로 변경 후 다시 실행

## 11. 정리

- 시작: `start-dev.bat` / `./start-dev.sh`
- 종료: `stop-dev.bat` / `./stop-dev.sh`
- 고급 제어: `python3 devctl.py ...`
