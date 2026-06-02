#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

IMAGE_NAME="${IMAGE_NAME:-kalshi-app}"
CONTAINER_NAME="${CONTAINER_NAME:-kalshi-app}"
APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8000}"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env}"
DOCKER_INTERNAL_KEY_PATH="/run/secrets/kalshi-private.key"

load_env() {
  if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  fi
}

usage() {
  cat <<'EOF'
Usage: ./run.sh <command>

Commands:
  help          Show this help message
  setup-env     Copy .env.example to .env if .env does not exist
  install       Install Python dependencies locally
  test          Run local compile checks and pytest
  local         Start the app locally with uvicorn
  docker-build  Build the Docker image
  docker-run    Run the Docker container on APP_PORT
  docker-stop   Stop and remove the running Docker container
  docker-logs   Tail Docker container logs

Environment variables read from .env when present:
  KALSHI_ENV
  KALSHI_API_KEY_ID
  KALSHI_PRIVATE_KEY_PATH
  KALSHI_PRIVATE_KEY
  HOST_KALSHI_PRIVATE_KEY_PATH
  KALSHI_REQUEST_TIMEOUT_SECONDS
  DEFAULT_MARKET_LIMIT
  DEFAULT_MAX_SPREAD_CENTS
  DEFAULT_MIN_DEPTH_CONTRACTS
  DEFAULT_ORDERBOOK_DEPTH_CENTS
  DEFAULT_MIN_VOLUME_24H
  DEFAULT_MIN_LIQUIDITY_DOLLARS
  APP_HOST
  APP_PORT

Docker note:
  In docker mode, you can either set HOST_KALSHI_PRIVATE_KEY_PATH to mount a key file
  or set KALSHI_PRIVATE_KEY in .env to pass the PEM contents directly as an env var.
  If a host key path is provided, the script mounts it and sets KALSHI_PRIVATE_KEY_PATH
  to /run/secrets/kalshi-private.key automatically.
EOF
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' is not installed." >&2
    exit 1
  fi
}

setup_env() {
  if [[ -f "$ENV_FILE" ]]; then
    echo ".env already exists at $ENV_FILE"
  else
    cp .env.example "$ENV_FILE"
    echo "Created $ENV_FILE from .env.example"
  fi
}

install_local() {
  require_command python3
  python3 -m pip install --no-input -r requirements.txt
}

run_tests() {
  require_command python3
  python3 -m py_compile app/*.py tests/*.py
  pytest -q
}

run_local() {
  require_command python3
  load_env
  echo "Starting local server on ${APP_HOST}:${APP_PORT}"
  exec python3 -m uvicorn app.main:app --host "$APP_HOST" --port "$APP_PORT"
}

docker_build() {
  require_command docker
  docker build -t "$IMAGE_NAME" .
}

docker_run() {
  require_command docker
  load_env

  local -a docker_args
  docker_args=(
    run --detach
    --name "$CONTAINER_NAME"
    --restart unless-stopped
    --env-file "$ENV_FILE"
    -e "APP_HOST=0.0.0.0"
    -e "APP_PORT=8000"
    -p "${APP_PORT}:8000"
  )

  if [[ -n "${HOST_KALSHI_PRIVATE_KEY_PATH:-}" ]]; then
    if [[ ! -f "$HOST_KALSHI_PRIVATE_KEY_PATH" ]]; then
      echo "Error: HOST_KALSHI_PRIVATE_KEY_PATH does not exist: $HOST_KALSHI_PRIVATE_KEY_PATH" >&2
      exit 1
    fi
    docker_args+=(
      -v "${HOST_KALSHI_PRIVATE_KEY_PATH}:${DOCKER_INTERNAL_KEY_PATH}:ro"
      -e "KALSHI_PRIVATE_KEY_PATH=${DOCKER_INTERNAL_KEY_PATH}"
    )
  fi

  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  docker "${docker_args[@]}" "$IMAGE_NAME"
  echo "Container started: $CONTAINER_NAME"
  echo "App URL: http://localhost:${APP_PORT}"
}

docker_stop() {
  require_command docker
  docker rm -f "$CONTAINER_NAME"
}

docker_logs() {
  require_command docker
  docker logs -f "$CONTAINER_NAME"
}

load_env || true

case "${1:-help}" in
  help|-h|--help)
    usage
    ;;
  setup-env)
    setup_env
    ;;
  install)
    install_local
    ;;
  test)
    run_tests
    ;;
  local)
    run_local
    ;;
  docker-build)
    docker_build
    ;;
  docker-run)
    docker_run
    ;;
  docker-stop)
    docker_stop
    ;;
  docker-logs)
    docker_logs
    ;;
  *)
    echo "Unknown command: ${1}" >&2
    usage
    exit 1
    ;;
esac
