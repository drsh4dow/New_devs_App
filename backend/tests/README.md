# Revenue regressions

Run from the repository root. Application code is unchanged; the current faults leave these tests failing.

## API

```bash
bash backend/tests/run.sh
# Focus one case:
bash backend/tests/run.sh -k month
```

Requires Docker Compose. Each run creates and removes its own PostgreSQL, Redis, network, and test container. It does not clear the development database or cache.

The tests call a running FastAPI server over HTTP, with real bearer-token verification and test-only signed identities for Sunset and Ocean. The login UI is not exercised. Reservation queries and revenue caching are not mocked.

Cases:

- Seeded Sunset total on load and refresh: 2,250.00 / 4 bookings.
- Both client request orders and refreshes: Sunset 2,250.00 / 4; Ocean 0.00 / 0.
- Paris and New York local month boundaries across March 2024 daylight saving. Request March, February, April, then March without clearing the cache.
- Three reservations of 0.335: sum first, then half-up rounding gives 1.01, not 1.02.

`month` and `year` are the approved reporting contract. The current endpoint ignores them. Database fallback currently masks the date-filtering and aggregate-rounding checks; their failures do not independently prove those causes.

## Revenue card

Requires frontend dependencies installed for your OS and `agent-browser` with Chromium. Start the test server in another terminal:

```bash
cd frontend
npm exec vite -- --config tests/vite.config.ts
```

This checkout contains tracked macOS dependencies. For this Linux run, we installed only the missing native binaries outside the worktree:

```bash
npm install --prefix /tmp/flex-revenue-native --ignore-scripts --no-audit --no-fund \
  @rollup/rollup-linux-x64-gnu@4.50.0 @esbuild/linux-x64@0.25.9
# In frontend, use this instead of the server command above:
NODE_PATH=/tmp/flex-revenue-native/node_modules npm exec vite -- --config tests/vite.config.ts
```

Then, from the repository root:

```bash
bash frontend/tests/run.sh
```

This renders the actual `RevenueSummary` and uses the actual frontend API client. The test server supplies controlled HTTP responses, not real account data. It checks 1.004 → 1.00 and 1.005 → 1.01. The script closes only its own browser session and exits nonzero on failure.

The agreed rules are property-local check-in month, exact summation, and half-up rounding of the final total. These rules are not specified in the original assignment.
