#!/usr/bin/env python3
"""Mocktalk 개발 스택 제어 스크립트"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
COMPOSE_FILE = ROOT_DIR / "docker-compose.yml"
ENV_FILE = ROOT_DIR / ".env.dev"
REPOSITORIES = {
    "backend": "https://github.com/OhSeongHyeon/mocktalkback.git",
    "frontend": "https://github.com/OhSeongHyeon/mocktalkfront.git",
}
REPO_REQUIRED_FILES = {
    "backend": ["Dockerfile", "README.md"],
    "frontend": ["Dockerfile", "README.md"],
}

# 번역: Python 3.8 이상이 필요합니다.
MSG_PYTHON_REQUIRED = "Python 3.8 or later is required."

# 번역: Docker Compose를 찾을 수 없습니다. Docker Desktop 또는 Docker Engine + Compose를 설치하세요.
MSG_COMPOSE_NOT_FOUND = (
    "Docker Compose was not found. Install Docker Desktop or Docker Engine with Compose."
)

# 번역: Docker를 사용할 수 없습니다. Docker Desktop 실행 상태를 확인하세요.
MSG_DOCKER_UNAVAILABLE = "Docker is not available. Check whether Docker Desktop is running."

# 번역: git이 설치되어 있지 않습니다. git 설치 후 다시 실행하세요.
MSG_GIT_NOT_FOUND = "git is not installed. Install git and run again."


def fail(message: str, code: int = 1) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(code)


def check_python_version() -> None:
    if sys.version_info < (3, 8):
        fail(MSG_PYTHON_REQUIRED)


def ensure_required_paths() -> None:
    if not COMPOSE_FILE.exists():
        # 번역: 컴포즈 파일이 없습니다.
        fail(f"Compose file not found: {COMPOSE_FILE}")
    if not ENV_FILE.exists():
        # 번역: 환경 파일이 없습니다.
        fail(f"Environment file not found: {ENV_FILE}")


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_quiet(command: list[str]) -> int:
    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode


def resolve_compose_command() -> list[str]:
    if command_exists("docker") and run_quiet(["docker", "compose", "version"]) == 0:
        return ["docker", "compose"]
    if command_exists("docker-compose"):
        return ["docker-compose"]
    fail(MSG_COMPOSE_NOT_FOUND)
    return []


def validate_repo_files(repo_name: str, repo_dir: Path) -> None:
    required_files = REPO_REQUIRED_FILES.get(repo_name, [])
    for required_file in required_files:
        if not (repo_dir / required_file).exists():
            # 번역: 디렉토리는 있지만 필수 파일이 없습니다.
            fail(
                f"{repo_name} directory exists but a required file is missing: "
                f"{repo_dir / required_file}"
            )


def clone_repo(repo_name: str, repo_url: str, repo_dir: Path) -> None:
    if not command_exists("git"):
        fail(MSG_GIT_NOT_FOUND)

    # 번역: 저장소가 없어 자동으로 내려받습니다.
    print(f"[INFO] Repository not found. Cloning {repo_name}: {repo_url}")
    result = subprocess.run(
        ["git", "clone", repo_url, str(repo_dir)],
        cwd=ROOT_DIR,
        check=False,
    )
    if result.returncode != 0:
        # 번역: 저장소 clone에 실패했습니다. git 출력 로그를 확인하세요.
        fail(f"Failed to clone repository: {repo_name}. Check git output for details.")


def pull_repo(repo_name: str, repo_dir: Path) -> None:
    if not command_exists("git"):
        fail(MSG_GIT_NOT_FOUND)

    if run_quiet(["git", "-C", str(repo_dir), "rev-parse", "--is-inside-work-tree"]) != 0:
        # 번역: 디렉토리가 git 저장소가 아닙니다.
        fail(f"Directory is not a git repository: {repo_dir}")

    # 번역: 저장소 최신 변경사항을 가져옵니다.
    print(f"[INFO] Pulling latest changes for {repo_name} (git pull --ff-only)")
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "pull", "--ff-only"],
        cwd=ROOT_DIR,
        check=False,
    )
    if result.returncode != 0:
        # 번역: 저장소 pull에 실패했습니다. 충돌 또는 로컬 변경사항을 확인하세요.
        fail(f"Failed to pull repository: {repo_name}. Check local changes or merge state.")


def ensure_repositories(should_pull: bool = False) -> None:
    for repo_name, repo_url in REPOSITORIES.items():
        repo_dir = ROOT_DIR / repo_name

        if repo_dir.exists() and not repo_dir.is_dir():
            # 번역: 경로가 디렉토리가 아닙니다.
            fail(f"Path exists but is not a directory: {repo_dir}")

        if not repo_dir.exists():
            clone_repo(repo_name, repo_url, repo_dir)
            validate_repo_files(repo_name, repo_dir)
            continue

        if repo_dir.exists() and not any(repo_dir.iterdir()):
            clone_repo(repo_name, repo_url, repo_dir)
            validate_repo_files(repo_name, repo_dir)
            continue

        validate_repo_files(repo_name, repo_dir)
        if should_pull:
            pull_repo(repo_name, repo_dir)
            validate_repo_files(repo_name, repo_dir)


def ensure_docker_available(compose_command: list[str]) -> None:
    if compose_command[0] == "docker":
        if run_quiet(["docker", "version"]) != 0:
            fail(MSG_DOCKER_UNAVAILABLE)


def compose_base_args(compose_command: list[str]) -> list[str]:
    return compose_command + [
        "--env-file",
        str(ENV_FILE),
        "-f",
        str(COMPOSE_FILE),
    ]


def run_compose(compose_command: list[str], compose_args: list[str]) -> int:
    full_command = compose_base_args(compose_command) + compose_args
    # 번역: 실행 명령어를 출력합니다.
    print("[RUN]", " ".join(full_command))
    completed = subprocess.run(full_command, cwd=ROOT_DIR, check=False)
    return completed.returncode


def load_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        with ENV_FILE.open("r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                    value = value[1:-1]
                values[key] = value
    except OSError:
        return {}
    return values


def get_url_from_env(env_values: dict[str, str], key: str, default_port: str) -> str:
    port = env_values.get(key, "").strip() or default_port
    return f"http://localhost:{port}"


def show_access_info() -> str:
    env_values = load_env_file()
    frontend_url = get_url_from_env(env_values, "FRONTEND_HOST_PORT", "8081")
    backend_url = get_url_from_env(env_values, "SERVER_PORT", "8082")
    prometheus_url = get_url_from_env(env_values, "PROMETHEUS_PORT", "9090")
    grafana_url = get_url_from_env(env_values, "GRAFANA_PORT", "3000")
    minio_console_url = get_url_from_env(env_values, "MINIO_CONSOLE_PORT", "9001")

    # 번역: 개발 스택 실행이 완료되었습니다.
    print("[INFO] Development stack is up.")
    # 번역: 프론트 주소입니다.
    print(f"[INFO] Frontend: {frontend_url}")
    # 번역: 백엔드 주소입니다.
    print(f"[INFO] Backend: {backend_url}")
    # 번역: Prometheus 주소입니다.
    print(f"[INFO] Prometheus: {prometheus_url}")
    # 번역: Grafana 주소입니다.
    print(f"[INFO] Grafana: {grafana_url}")
    # 번역: MinIO Console 주소입니다.
    print(f"[INFO] MinIO Console: {minio_console_url}")

    return frontend_url


def open_frontend_in_browser(url: str) -> None:
    # 번역: 브라우저에서 프론트 주소를 엽니다.
    print(f"[INFO] Opening frontend in browser: {url}")
    opened = webbrowser.open(url, new=2)
    if not opened:
        # 번역: 브라우저 자동 열기에 실패했습니다. 주소를 수동으로 여세요.
        print(f"[WARN] Failed to open browser automatically. Open this URL manually: {url}")


def after_stack_up(args: argparse.Namespace, exit_code: int) -> int:
    if exit_code != 0:
        return exit_code
    frontend_url = show_access_info()
    if bool(getattr(args, "open", False)):
        open_frontend_in_browser(frontend_url)
    return exit_code


def cmd_up(args: argparse.Namespace, compose_command: list[str]) -> int:
    compose_args = ["up"]
    if args.detached:
        compose_args.append("-d")
    if not args.no_build:
        compose_args.append("--build")
    exit_code = run_compose(compose_command, compose_args)
    return after_stack_up(args, exit_code)


def cmd_down(args: argparse.Namespace, compose_command: list[str]) -> int:
    compose_args = ["down", "--remove-orphans"]
    if args.volumes:
        compose_args.append("--volumes")
    return run_compose(compose_command, compose_args)


def cmd_restart(args: argparse.Namespace, compose_command: list[str]) -> int:
    down_code = run_compose(compose_command, ["down", "--remove-orphans"])
    if down_code != 0:
        return down_code

    up_args = ["up"]
    if args.detached:
        up_args.append("-d")
    if not args.no_build:
        up_args.append("--build")
    exit_code = run_compose(compose_command, up_args)
    return after_stack_up(args, exit_code)


def cmd_status(_: argparse.Namespace, compose_command: list[str]) -> int:
    return run_compose(compose_command, ["ps"])


def cmd_logs(args: argparse.Namespace, compose_command: list[str]) -> int:
    compose_args = ["logs"]
    if args.follow:
        compose_args.append("-f")
    if args.service:
        compose_args.append(args.service)
    return run_compose(compose_command, compose_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mocktalk development stack controller")
    subparsers = parser.add_subparsers(dest="command", required=True)

    up_parser = subparsers.add_parser("up", help="Start the full stack")
    up_parser.add_argument("--no-build", action="store_true", help="Start without image build")
    up_parser.add_argument("--foreground", action="store_true", help="Run in foreground")
    up_parser.add_argument("--pull", action="store_true", help="Run git pull --ff-only before start")
    up_parser.add_argument("--open", action="store_true", help="Open frontend URL in browser after start")
    up_parser.set_defaults(handler=cmd_up)

    down_parser = subparsers.add_parser("down", help="Stop and clean the full stack")
    down_parser.add_argument("--volumes", action="store_true", help="Also remove volumes")
    down_parser.set_defaults(handler=cmd_down)

    restart_parser = subparsers.add_parser("restart", help="Restart the full stack")
    restart_parser.add_argument("--no-build", action="store_true", help="Restart without image build")
    restart_parser.add_argument("--foreground", action="store_true", help="Restart in foreground")
    restart_parser.add_argument("--pull", action="store_true", help="Run git pull --ff-only before restart")
    restart_parser.add_argument("--open", action="store_true", help="Open frontend URL in browser after restart")
    restart_parser.set_defaults(handler=cmd_restart)

    status_parser = subparsers.add_parser("status", help="Show container status")
    status_parser.set_defaults(handler=cmd_status)

    logs_parser = subparsers.add_parser("logs", help="Show logs")
    logs_parser.add_argument("service", nargs="?", help="Specific service name")
    logs_parser.add_argument("-f", "--follow", action="store_true", help="Follow logs in real time")
    logs_parser.set_defaults(handler=cmd_logs)

    return parser


def main() -> int:
    check_python_version()
    parser = build_parser()
    args = parser.parse_args()
    ensure_required_paths()
    ensure_repositories(should_pull=bool(getattr(args, "pull", False)))

    # 기본 동작은 백그라운드 실행으로 맞춘다.
    if hasattr(args, "foreground"):
        args.detached = not args.foreground

    compose_command = resolve_compose_command()
    ensure_docker_available(compose_command)

    handler = args.handler
    return handler(args, compose_command)


if __name__ == "__main__":
    raise SystemExit(main())
