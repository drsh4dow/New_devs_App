"""Revenue API regressions. Run with bash backend/tests/run.sh."""

import json
import os
import time
import unittest
from decimal import Decimal
from pathlib import Path

import httpx
import psycopg2
import redis
from jose import jwt


class RevenueTests(unittest.TestCase):
    def setUp(self):
        self.db = psycopg2.connect(os.environ["DATABASE_URL"])
        self.addCleanup(self.db.close)
        if self.db.info.dbname != "revenue_test":
            raise RuntimeError("Use the isolated database from tests/compose.yml")
        self.db.autocommit = True
        with self.db.cursor() as cursor:
            cursor.execute("TRUNCATE reservations, properties, tenants CASCADE")
            cursor.execute(
                (Path(__file__).parents[1] / "database/seed.sql").read_text()
            )

        self.cache = redis.Redis.from_url(os.environ["REDIS_URL"])
        self.addCleanup(self.cache.close)
        self.cache.flushdb()
        self.client = httpx.Client(base_url="http://api:8000")
        self.addCleanup(self.client.close)

    def get(self, client, path, **params):
        # Same claims as the assignment logins, signed only for the isolated API.
        tenant = {"sunset": "tenant-a", "ocean": "tenant-b"}[client]
        token = jwt.encode(
            {
                "id": f"user-{client}",
                "email": f"{client}@propertyflow.com",
                "aud": "authenticated",
                "exp": int(time.time()) + 60,
                "app_metadata": {"role": "user", "tenant_id": tenant},
            },
            os.environ["SECRET_KEY"],
            algorithm="HS256",
        )
        return self.client.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )

    def summary(self, client, property_id="prop-001", currency="USD", **period):
        response = self.get(
            client, "/api/v1/dashboard/summary", property_id=property_id, **period
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["property_id"], property_id)
        self.assertEqual(data["currency"], currency)
        return Decimal(str(data["total_revenue"])), data["reservations_count"]

    def replace_reservations(self, rows):
        """Each row is (tenant, UTC check-in, exact amount)."""
        with self.db.cursor() as cursor:
            cursor.execute("DELETE FROM reservations")
            cursor.executemany(
                """
                INSERT INTO reservations
                    (id, property_id, tenant_id, check_in_date, check_out_date, total_amount)
                VALUES (%s, 'prop-001', %s, %s, %s::timestamptz + INTERVAL '1 day', %s)
                """,
                [
                    (f"test-{index}", tenant, check_in, check_in, amount)
                    for index, (tenant, check_in, amount) in enumerate(rows)
                ],
            )

    def test_sunset_total_comes_from_reservations_on_load_and_refresh(self):
        # Seed: 1250.000 + 333.333 + 333.333 + 333.334 = 2250.000.
        results = [self.summary("sunset") for _ in range(2)]
        self.assertEqual(results, [(Decimal("2250.00"), 4)] * 2)

    def test_clients_keep_their_own_totals_in_either_request_order(self):
        expected = {
            "sunset": (Decimal("2250.00"), 4),
            "ocean": (Decimal("0.00"), 0),
        }
        for order in [("sunset", "ocean"), ("ocean", "sunset")]:
            with self.subTest(first_client=order[0]):
                self.cache.flushdb()
                # A deployment must not reuse unscoped entries from the old code.
                self.cache.set(
                    "revenue:prop-001",
                    json.dumps(
                        {
                            "property_id": "prop-001",
                            "tenant_id": "tenant-a",
                            "total": "1000.00",
                            "currency": "USD",
                            "count": 3,
                        }
                    ),
                )
                # Repeat both requests: a refresh must not change ownership.
                clients = order * 2
                results = [self.summary(client) for client in clients]
                self.assertEqual(results, [expected[client] for client in clients])

    def test_property_selection_is_scoped_to_the_client(self):
        for client, expected, other_property in [
            (
                "sunset",
                [
                    "Beach House Alpha",
                    "City Apartment Downtown",
                    "Country Villa Estate",
                ],
                "prop-004",
            ),
            (
                "ocean",
                ["Mountain Lodge Beta", "Lakeside Cottage", "Urban Loft Modern"],
                "prop-002",
            ),
        ]:
            with self.subTest(client=client):
                response = self.get(client, "/api/v1/dashboard/properties")
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual([item["name"] for item in response.json()], expected)
                response = self.get(
                    client, "/api/v1/dashboard/summary", property_id=other_property
                )
                self.assertEqual(response.status_code, 404)

    def test_database_failure_does_not_return_or_cache_sample_revenue(self):
        with self.db.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE reservations RENAME TO unavailable_reservations"
            )
            try:
                response = self.get(
                    "sunset", "/api/v1/dashboard/summary", property_id="prop-001"
                )
                self.assertEqual(response.status_code, 500)
                self.assertEqual(list(self.cache.scan_iter("revenue:*")), [])
            finally:
                cursor.execute(
                    "ALTER TABLE unavailable_reservations RENAME TO reservations"
                )

    def test_currency_is_preserved_and_mixed_currencies_are_not_added(self):
        with self.db.cursor() as cursor:
            cursor.execute("UPDATE reservations SET currency = 'EUR'")
            self.assertEqual(
                self.summary("sunset", currency="EUR"), (Decimal("2250.00"), 4)
            )
            cursor.execute(
                "UPDATE reservations SET currency = 'USD' WHERE id = 'res-tz-1'"
            )
        self.cache.flushdb()
        response = self.get(
            "sunset", "/api/v1/dashboard/summary", property_id="prop-001"
        )
        self.assertEqual(response.status_code, 422)

    def test_month_uses_property_timezone_across_daylight_saving(self):
        # One instant before / exactly at local March and April midnight.
        # Both properties change UTC offset during March 2024.
        cases = [
            (
                "sunset",
                "tenant-a",
                [
                    "2024-02-29T22:59:59.999999Z",  # Paris: February
                    "2024-02-29T23:00:00Z",  # Paris: March 1, 00:00
                    "2024-03-31T21:59:59.999999Z",  # Paris: March
                    "2024-03-31T22:00:00Z",  # Paris: April 1, 00:00
                ],
            ),
            (
                "ocean",
                "tenant-b",
                [
                    "2024-03-01T04:59:59.999999Z",  # New York: February
                    "2024-03-01T05:00:00Z",  # New York: March 1, 00:00
                    "2024-04-01T03:59:59.999999Z",  # New York: March
                    "2024-04-01T04:00:00Z",  # New York: April 1, 00:00
                ],
            ),
        ]
        for client, tenant, instants in cases:
            with self.subTest(client=client):
                self.cache.flushdb()
                self.replace_reservations(
                    [
                        (tenant, instant, amount)
                        for instant, amount in zip(
                            instants, ["1.00", "2.00", "4.00", "8.00"]
                        )
                    ]
                )
                # Switch month without clearing Redis, then return to March.
                results = [
                    self.summary(client, month=month, year=2024)
                    for month in [3, 2, 4, 3]
                ]
                self.assertEqual(
                    results,
                    [
                        (Decimal("6.00"), 2),
                        (Decimal("1.00"), 1),
                        (Decimal("8.00"), 1),
                        (Decimal("6.00"), 2),
                    ],
                )

    def test_total_is_rounded_once_after_summing_reservations(self):
        # Exact sum: 1.005 → 1.01 half-up. Rounding each row gives 1.02.
        self.replace_reservations(
            [
                ("tenant-a", "2024-03-15T10:00:00Z", "0.335"),
                ("tenant-a", "2024-03-16T10:00:00Z", "0.335"),
                ("tenant-a", "2024-03-17T10:00:00Z", "0.335"),
            ]
        )
        results = [self.summary("sunset") for _ in range(2)]
        self.assertEqual(results, [(Decimal("1.01"), 3)] * 2)
