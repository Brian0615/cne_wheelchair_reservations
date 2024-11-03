WITH validate_rental AS (SELECT check_if_rental_exists({rental_id}))

UPDATE {schema}.{table}
SET device_id = {device_id}
WHERE id = {rental_id};