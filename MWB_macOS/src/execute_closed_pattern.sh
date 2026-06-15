#!/usr/bin/env bash
set -e

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_BIN="$BASE_DIR/BideSpanTree/bin/bidespantree"

TARGET_PATH="$1"
if [[ "$TARGET_PATH" != /* ]]; then
  TARGET_PATH="$BASE_DIR/$TARGET_PATH"
fi

mkdir -p "$(dirname "$TARGET_PATH")"

if [[ -x "$LOCAL_BIN" ]]; then
  if (cd "$BASE_DIR/BideSpanTree/bin" && ./bidespantree > "$TARGET_PATH"); then
    exit 0
  fi
fi

TARGET_REL="${TARGET_PATH#$BASE_DIR/}"
DOCKER_TARGET="/data/$TARGET_REL"

docker run --rm --platform linux/amd64 \
  -v "$BASE_DIR:/data" \
  ubuntu:22.04 \
  bash -c "
    cd /data/BideSpanTree/bin &&
    chmod +x bidespantree &&
    mkdir -p \"\$(dirname '$DOCKER_TARGET')\" &&
    ./bidespantree > '$DOCKER_TARGET'
  "
