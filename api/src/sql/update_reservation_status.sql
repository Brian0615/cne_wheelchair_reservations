WITH check_reservation AS (SELECT {schema}.check_if_reservation_exists({reservation_id}))

UPDATE {schema}.{table}
SET status = {status}
WHERE id = {reservation_id}
