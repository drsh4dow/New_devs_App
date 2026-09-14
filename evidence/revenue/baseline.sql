-- Read-only baseline from the seeded database.
-- Run: docker compose exec -T db psql -U postgres -d propertyflow < evidence/revenue/baseline.sql
\pset pager off

SELECT p.tenant_id, p.id AS property_id, p.name, p.timezone,
       COUNT(r.id) AS reservations_count,
       COALESCE(SUM(r.total_amount), 0) AS total_revenue
FROM properties AS p
LEFT JOIN reservations AS r
  ON r.property_id = p.id AND r.tenant_id = p.tenant_id
GROUP BY p.tenant_id, p.id, p.name, p.timezone
ORDER BY p.tenant_id, p.id;

-- March uses the property's local check-in date for this comparison.
SELECT p.tenant_id, p.id AS property_id,
       COUNT(r.id) AS march_reservations_count,
       COALESCE(SUM(r.total_amount), 0) AS march_revenue
FROM properties AS p
LEFT JOIN reservations AS r
  ON r.property_id = p.id AND r.tenant_id = p.tenant_id
 AND r.check_in_date >= (TIMESTAMP '2024-03-01' AT TIME ZONE p.timezone)
 AND r.check_in_date < (TIMESTAMP '2024-04-01' AT TIME ZONE p.timezone)
GROUP BY p.tenant_id, p.id
ORDER BY p.tenant_id, p.id;
