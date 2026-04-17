#!/usr/bin/env bash
set -e
os="$(uname)"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$os" = "Darwin" ];then
  docker run --rm --platform linux/amd64 \
    -v "$BASE_DIR:/data" \
    ubuntu:22.04 \
    bash -c "
      cd /data/BideSpanTree/bin &&
      chmod +x bidespantree &&
      ./bidespantree > /data/Patterns_results/Closed/$1
    "
    echo "Running BideSpanTree in a Docker container"
else
  echo "Running BideSpanTree natively";
      cd "./BideSpanTree/bin";
      ./bidespantree > "../../Patterns_results/Closed/$1";
  echo "$(ls)";
      cd ../..;
fi