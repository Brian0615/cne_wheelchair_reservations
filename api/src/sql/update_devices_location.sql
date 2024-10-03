WITH validate_device AS (SELECT check_if_device_exists({device_id}))

UPDATE {schema}.{table}
SET location = {location}
WHERE id = {device_id};
