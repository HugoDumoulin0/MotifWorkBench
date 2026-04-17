#!/usr/bin/env bash
set -e

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

docker run --rm --platform linux/amd64 \
  -v "$BASE_DIR:/data" \
  ubuntu:22.04 \
  bash -c "
    cd /data/BideSpanTree/bin &&
    chmod +x bidespantree &&
    ./bidespantree > /data/Patterns_results/Closed/$1
  "