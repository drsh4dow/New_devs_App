# Revenue reproduction evidence

Baseline captured on 2026-09-14 with unchanged application code and separate browser sessions for Sunset and Ocean. Findings and later regression results: [AUTHOR_NOTES.md](../AUTHOR_NOTES.md).

## What the clients saw

| Client / `prop-001` | Database total / bookings | Dashboard total / bookings | Screenshot |
| --- | --- | --- | --- |
| Sunset | USD 2,250.00 / 4 | USD 1,000.00 / 3 | [Sunset](01-sunset-prop-001.png) |
| Ocean | USD 0.00 / 0 | USD 1,000.00 / 3 | [Ocean](02-ocean-prop-001.png) |

Refreshing preserved both faults. The refresh screenshots were byte-for-byte identical to the first screenshots, so only one per client is retained.

The backend failed to initialise the database pool, then returned sample values with HTTP 200. Ocean authenticated as `tenant-b` but received the cache entry created for `tenant-a`. Equal response totals alone would not prove cache reuse: the captures below also identify the authenticated clients, cached owner and Redis reads.

These baseline screenshots do not prove a timezone or cents fault. The displayed total is a fixed sample value.

## Repeat the comparison

1. Start with an empty revenue cache in the development environment.
2. Run the read-only [database baseline](baseline.sql):

   ```bash
   docker compose exec -T db psql -U postgres -d propertyflow < evidence/revenue/baseline.sql
   ```

3. Log in as Sunset at `http://127.0.0.1:3000/login`. Keep `prop-001` selected.
4. In a separate browser session, log in as Ocean within five minutes. Keep `prop-001` selected.
5. Compare each dashboard with the table above, then refresh both pages.

The March baseline uses each property's local check-in month. With this seed data, March and all-time totals are equal. Repeatable regression commands are in [the test README](../../backend/tests/README.md).

## Environment used

The standard frontend build failed during the Supabase CLI postinstall download (`Z_DATA_ERROR`). The temporary Dockerfile uses `npm install --ignore-scripts && npm rebuild esbuild`. The temporary Compose override binds IPv4 because another project occupies `[::1]:3000`.

```bash
docker compose -f docker-compose.yml -f /tmp/flex-assignment-repro.compose.yml up --build
```

The override depends on `/tmp/flex-assignment-frontend.Dockerfile`. Keep both setup files while using this environment. The live log, `/tmp/flex-assignment-docker-repro.log`, can contain authentication details and must not be published.

## Captured evidence

The original text captures are consolidated below. No credentials or bearer tokens are included.

<details>
<summary>Database baseline</summary>

```text
Pager usage is off.
 tenant_id | property_id |          name           |     timezone     | reservations_count | total_revenue
-----------+-------------+-------------------------+------------------+--------------------+---------------
 tenant-a  | prop-001    | Beach House Alpha       | Europe/Paris     |                  4 |      2250.000
 tenant-a  | prop-002    | City Apartment Downtown | Europe/Paris     |                  4 |      4975.500
 tenant-a  | prop-003    | Country Villa Estate    | Europe/Paris     |                  2 |      6100.500
 tenant-b  | prop-001    | Mountain Lodge Beta     | America/New_York |                  0 |             0
 tenant-b  | prop-004    | Lakeside Cottage        | America/New_York |                  4 |      1776.500
 tenant-b  | prop-005    | Urban Loft Modern       | America/New_York |                  3 |      3256.000
(6 rows)

 tenant_id | property_id | march_reservations_count | march_revenue
-----------+-------------+--------------------------+---------------
 tenant-a  | prop-001    |                        4 |      2250.000
 tenant-a  | prop-002    |                        4 |      4975.500
 tenant-a  | prop-003    |                        2 |      6100.500
 tenant-b  | prop-001    |                        0 |             0
 tenant-b  | prop-004    |                        4 |      1776.500
 tenant-b  | prop-005    |                        3 |      3256.000
(6 rows)
```

</details>

<details>
<summary>API responses</summary>

Sunset:

```json
{
  "method": "GET",
  "url": "http://localhost:8000/api/v1/dashboard/summary?property_id=prop-001&_t=1789397778899",
  "status": 200,
  "responseBody": "{\"property_id\":\"prop-001\",\"total_revenue\":1000.0,\"currency\":\"USD\",\"reservations_count\":3}"
}
```

Ocean after refresh:

```json
{
  "method": "GET",
  "url": "http://localhost:8000/api/v1/dashboard/summary?property_id=prop-001&_t=1789397853181",
  "status": 200,
  "responseBody": "{\"property_id\":\"prop-001\",\"total_revenue\":1000.0,\"currency\":\"USD\",\"reservations_count\":3}"
}
```

</details>

<details>
<summary>Backend events and cache ownership</summary>

```text
backend-1   | INFO:app.core.auth:AUTH: OK - sunset@propertyflow.com (ID: user-sunset) in 0.00s, tenant=tenant-a, cities=0, perms=0
backend-1   | ERROR:app.core.database_pool:❌ Database pool initialization failed: 'Settings' object has no attribute 'supabase_db_user'
backend-1   | Database error for prop-001 (tenant: tenant-a): Database pool not available
backend-1   | INFO:     172.18.0.1:37312 - "GET /api/v1/dashboard/summary?property_id=prop-001&_t=1789397778899 HTTP/1.1" 200 OK
backend-1   | INFO:app.core.auth:AUTH: OK - ocean@propertyflow.com (ID: user-ocean) in 0.00s, tenant=tenant-b, cities=0, perms=0
backend-1   | INFO:     172.18.0.1:36066 - "GET /api/v1/dashboard/summary?property_id=prop-001&_t=1789397823330 HTTP/1.1" 200 OK
backend-1   | INFO:     172.18.0.1:36434 - "GET /api/v1/dashboard/summary?property_id=prop-001&_t=1789397853181 HTTP/1.1" 200 OK
backend-1   | INFO:     172.18.0.1:43148 - "GET /api/v1/dashboard/summary?property_id=prop-001&_t=1789397874658 HTTP/1.1" 200 OK
```

Redis entry after Ocean's request:

```json
{"property_id": "prop-001", "tenant_id": "tenant-a", "total": "1000.00", "currency": "USD", "count": 3}
```

Redis monitoring during refresh:

```text
1789397853.133437 [0 127.0.0.1:59764] "GET" "revenue:prop-001"
1789397853.185775 [0 172.18.0.4:34640] "GET" "revenue:prop-001"
1789397874.663885 [0 172.18.0.4:34640] "GET" "revenue:prop-001"
```

The first read was our inspection. The other reads came from the backend, without a new cache write.

</details>
