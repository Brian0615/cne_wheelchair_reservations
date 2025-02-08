WITH validate_device AS (SELECT {schema}.check_if_device_exists({device_id}))

DELETE
FROM {schema}.{table}
WHERE id = {device_id};
