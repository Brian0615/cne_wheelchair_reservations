WITH validate_rental AS (SELECT {schema}.check_if_rental_exists({rental_id}))

UPDATE {schema}.{table}
SET device_id = {device_id}
WHERE id = {rental_id};