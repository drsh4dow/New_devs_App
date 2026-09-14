# Author Notes

We used Pi to trace the revenue request, then compared both clients with the database in Docker. Evidence: `evidence/revenue/README.md`.

## Wrong totals

Sunset's `prop-001`: database 2,250.00 / 4 reservations; dashboard 1,000.00 / 3, including after refresh.

Database setup reads the missing `supabase_db_user` setting. The calculation fails and returns fixed sample values with HTTP 200. The missing 1,250.00 is not proof of a timezone fault.

## Client data isolation

Both clients have a different `prop-001`, but Redis uses one key: `revenue:prop-001`.

Ocean authenticates as `tenant-b` and receives the entry created for `tenant-a`. We checked the authenticated client, cached owner and response; equal totals alone would not prove this. Ocean should receive 0.00 / 0 bookings.

## Reporting month

The dashboard says monthly but calls an all-time calculation. The monthly function is unused and returns zero.

We agreed to use the property's local check-in month. Paris's `2024-02-29 23:30 UTC` reservation belongs to March.

Tests cover Paris and New York month boundaries, daylight saving and switching months without clearing Redis. They still receive sample values, so timezone calculation remains unverified.

## Cents

We agreed to sum exact amounts, then round the final total half-up. Three amounts of 0.335 should give 1.01, not the 1.02 produced by rounding each reservation.

A controlled HTTP response of 1.005 makes the real card show 1.00 instead of 1.01. The 1.004 control passes. The HTTP value is correct; JavaScript's `1.005 * 100` produces `100.49999999999999` and rounds down. Formatting 1.01 preserves it.

This reproduces a cents fault with controlled data, not the original seeded totals.

## Regression results

- API: 4 tests, 6 failing cases. Covers totals, refresh, both client orders, month boundaries and aggregate rounding. Database fallback still masks the latter two.
- Real card: below-half-cent passes; half-cent fails.

Commands and setup: `backend/tests/README.md`. Application code is unchanged; these are the checks to repeat after each fix.
