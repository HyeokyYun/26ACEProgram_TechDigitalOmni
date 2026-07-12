#!/usr/bin/env bash
# adiFit 자동 재시작 감시 실행 + 크래시 스택 캡처.
# streamlit이 세그폴트로 죽으면 로그에 스택을 남기고 1초 후 재시작한다.
cd "$(dirname "$0")"

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export KMP_DUPLICATE_LIB_OK=TRUE
export TOKENIZERS_PARALLELISM=false
export PYTHONFAULTHANDLER=1
export PYTHONPATH=src

LOG="${ADIFIT_LOG:-/tmp/adifit_supervised.log}"
PORT="${PORT:-8501}"

while true; do
  echo "=== [START $(date '+%H:%M:%S')] ===" >> "$LOG"
  ./.venv/bin/streamlit run app.py \
    --server.headless true \
    --server.port "$PORT" \
    --server.fileWatcherType none >> "$LOG" 2>&1
  code=$?
  echo "=== [EXIT code=$code at $(date '+%H:%M:%S')] ===" >> "$LOG"
  sleep 1
done
