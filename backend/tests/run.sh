#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Separate containers, network and database for each run. No development ports.
project="revenue-tests-$(date +%s)-$$"
compose=(docker compose -p "$project" -f compose.yml)
trap '"${compose[@]}" down --volumes --remove-orphans --rmi local >/dev/null 2>&1' EXIT

"${compose[@]}" run --build --rm tests python -B -m unittest discover -s tests -v "$@"
