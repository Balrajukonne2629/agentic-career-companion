#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
BACKEND_STATIC_DIR="${SCRIPT_DIR}/static"

if [ ! -d "${FRONTEND_DIR}" ]; then
  echo "Frontend directory not found: ${FRONTEND_DIR}" >&2
  exit 1
fi

if [ ! -d "${FRONTEND_DIR}/dist" ]; then
  echo "Frontend build output not found. Run 'npm run build' in frontend first." >&2
  exit 1
fi

rm -rf "${BACKEND_STATIC_DIR}"
mkdir -p "${BACKEND_STATIC_DIR}"
cp -R "${FRONTEND_DIR}/dist/." "${BACKEND_STATIC_DIR}/"

echo "Frontend build copied to backend/static."