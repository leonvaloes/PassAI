#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG_FILE="$RUN_DIR/backend.log"
FRONTEND_LOG_FILE="$RUN_DIR/frontend.log"
DATA_DIR="$ROOT_DIR/data"
OUTPUT_DIR="$ROOT_DIR/output/generated"
BACKEND_URL="http://127.0.0.1:8000/health"
FRONTEND_URL="http://127.0.0.1:5173"
FOLLOW_LOGS=1

if [[ "${1:-}" == "--detach" ]]; then
  FOLLOW_LOGS=0
fi

resolve_win_pid() {
  local shell_pid="$1"
  if [[ -f "/proc/$shell_pid/winpid" ]]; then
    cat "/proc/$shell_pid/winpid"
  else
    echo "$shell_pid"
  fi
}

show_log_excerpt() {
  local label="$1"
  local log_file="$2"

  if [[ -f "$log_file" ]]; then
    echo
    echo "---- $label ($log_file) ----"
    sed -n '1,160p' "$log_file"
    echo "---- fim de $label ----"
  fi
}

stop_tracked_pid() {
  local pid_file="$1"
  local pid

  [[ -f "$pid_file" ]] || return 0
  pid="$(<"$pid_file")"

  if command -v taskkill.exe >/dev/null 2>&1; then
    taskkill.exe //PID "$pid" //T //F >/dev/null 2>&1 || true
  else
    kill "$pid" >/dev/null 2>&1 || true
  fi

  rm -f "$pid_file"
}

is_pid_running() {
  local pid="$1"
  if command -v tasklist.exe >/dev/null 2>&1; then
    tasklist.exe //FI "PID eq $pid" 2>/dev/null | grep -q "$pid"
  else
    kill -0 "$pid" >/dev/null 2>&1
  fi
}

prepare_pid_file() {
  local pid_file="$1"
  local service_name="$2"
  local pid

  [[ -f "$pid_file" ]] || return 0
  pid="$(<"$pid_file")"

  if is_pid_running "$pid"; then
    echo "$service_name parece ja estar em execucao. Use ./stop.sh antes de subir novamente."
    exit 1
  fi

  rm -f "$pid_file"
}

wait_for_url() {
  local url="$1"
  local attempts="$2"
  local attempt

  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if curl --silent --show-error --fail "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  return 1
}

fail_start() {
  local message="$1"

  echo
  echo "Falha ao subir o projeto: $message"
  show_log_excerpt "backend.log" "$BACKEND_LOG_FILE"
  show_log_excerpt "frontend.log" "$FRONTEND_LOG_FILE"
  stop_tracked_pid "$FRONTEND_PID_FILE"
  stop_tracked_pid "$BACKEND_PID_FILE"
  exit 1
}

follow_logs() {
  trap 'echo; echo "Monitor encerrado. Os servicos continuam rodando. Use ./stop.sh para derrubar."; exit 0' INT TERM
  echo
  echo "Monitorando logs. Pressione Ctrl+C para sair deste monitor sem derrubar os servicos."
  echo
  tail -n 20 -f "$BACKEND_LOG_FILE" "$FRONTEND_LOG_FILE"
}

mkdir -p "$RUN_DIR" "$DATA_DIR" "$OUTPUT_DIR"

prepare_pid_file "$BACKEND_PID_FILE" "Backend"
prepare_pid_file "$FRONTEND_PID_FILE" "Frontend"
rm -f "$BACKEND_LOG_FILE" "$FRONTEND_LOG_FILE"

[[ -d "$ROOT_DIR/venv" ]] || fail_start "ambiente virtual nao encontrado em $ROOT_DIR/venv"
[[ -x "$ROOT_DIR/venv/Scripts/python.exe" ]] || fail_start "python do venv nao encontrado em $ROOT_DIR/venv/Scripts/python.exe"
[[ -d "$ROOT_DIR/frontend/node_modules" ]] || fail_start "dependencias do frontend nao encontradas. Execute: cd frontend && npm install"
[[ -f "$ROOT_DIR/frontend/node_modules/vite/bin/vite.js" ]] || fail_start "vite nao encontrado em frontend/node_modules"
command -v node >/dev/null 2>&1 || fail_start "Node.js nao encontrado no PATH"
command -v curl >/dev/null 2>&1 || fail_start "curl nao encontrado no PATH"

echo "Subindo backend..."
(
  cd "$ROOT_DIR"
  PASSAI_DATA_FILE="$DATA_DIR/passai_state.json" \
  PASSAI_OUTPUT_DIR="$OUTPUT_DIR" \
  exec "$ROOT_DIR/venv/Scripts/python.exe" backend/server.py
) >"$BACKEND_LOG_FILE" 2>&1 &
BACKEND_PID="$(resolve_win_pid "$!")"
echo "$BACKEND_PID" >"$BACKEND_PID_FILE"

if ! wait_for_url "$BACKEND_URL" 20; then
  fail_start "backend nao respondeu em $BACKEND_URL"
fi

echo "Subindo frontend..."
(
  cd "$ROOT_DIR/frontend"
  exec node "$ROOT_DIR/frontend/node_modules/vite/bin/vite.js" --host 127.0.0.1 --port 5173
) >"$FRONTEND_LOG_FILE" 2>&1 &
FRONTEND_PID="$(resolve_win_pid "$!")"
echo "$FRONTEND_PID" >"$FRONTEND_PID_FILE"

if ! wait_for_url "$FRONTEND_URL" 20; then
  fail_start "frontend nao respondeu em $FRONTEND_URL"
fi

echo
echo "Pronto."
echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://127.0.0.1:5173"
echo "Logs:     $RUN_DIR"

if [[ "$FOLLOW_LOGS" -eq 1 && -t 1 ]]; then
  follow_logs
fi
