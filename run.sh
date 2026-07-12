#!/usr/bin/env bash
# adiFit 안정 실행 스크립트.
# Python 3.14 + macOS에서 sklearn/BLAS의 OpenMP 스레드 충돌로 인한 세그폴트(exit 139)를
# 막기 위해 네이티브 스레드를 1개로 제한하고 파일와처를 끈다.
set -e
cd "$(dirname "$0")"

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export KMP_DUPLICATE_LIB_OK=TRUE
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH=src

exec ./.venv/bin/streamlit run app.py \
  --server.headless true \
  --server.port "${PORT:-8501}" \
  --server.fileWatcherType none
