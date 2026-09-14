#!/usr/bin/env bash
set -euo pipefail

# Start Vite first: cd frontend && npm exec vite -- --config tests/vite.config.ts
url="${1:-http://127.0.0.1:5179}"
AGENT_BROWSER_SESSION="revenue-cents-$(date +%s)-$$"
export AGENT_BROWSER_SESSION
trap 'agent-browser close >/dev/null 2>&1' EXIT

failed=0
for example in 'below-half-cent:1.00' 'half-cent:1.01'; do
    property="${example%:*}"
    expected="${example#*:}"
    agent-browser open "$url/tests/revenue-card.html?property=$property" >/dev/null
    agent-browser wait --text 'Total Revenue' >/dev/null
    text="$(agent-browser get text '#root')"
    if grep -Fq "USD $expected" <<< "$text"; then
        printf 'PASS: %s → displayed USD %s\n' "$property" "$expected"
    else
        printf 'FAIL: %s → expected USD %s\n%s\n' "$property" "$expected" "$text"
        failed=1
    fi
done
exit "$failed"
