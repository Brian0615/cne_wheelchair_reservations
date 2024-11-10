WITH validate_device AS (SELECT {schema}.check_if_device_exists({device_id}))

UPDATE {schema}.{table}
SET location = {location}
WHERE id = {device_id};
