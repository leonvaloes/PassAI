#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"

stop_pid() {
  name="$1"
  pid_file="$2"

  if [ ! -f "$pid_file" ]; then
    echo "$name: PID nao encontrado."
    return
  fi

  pid="$(cat "$pid_file")"

  if command -v taskkill.exe >/dev/null 2>&1; then
    if taskkill.exe //PID "$pid" //T //F >/dev/null 2>&1; then
      echo "$name parado. PID $pid"
    else
      echo "$name ja nao estava rodando. PID $pid"
    fi
  elif kill "$pid" >/dev/null 2>&1; then
    echo "$name parado. PID $pid"
  else
    echo "$name ja nao estava rodando. PID $pid"
  fi

  rm -f "$pid_file"
}

stop_pid "Frontend" "$FRONTEND_PID_FILE"
stop_pid "Backend" "$BACKEND_PID_FILE"

if [ -d "$RUN_DIR" ] && [ -z "$(find "$RUN_DIR" -maxdepth 1 -name '*.pid' -print -quit)" ]; then
  rm -f "$RUN_DIR"/*.log 2>/dev/null || true
  rmdir "$RUN_DIR" 2>/dev/null || true
fi
