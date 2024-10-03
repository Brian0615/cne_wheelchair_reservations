WITH validate_device AS (SELECT check_if_device_exists({id}))

UPDATE {schema}.{table}
SET location = {location},
    status   = {status}
WHERE id = {id}
  AND type = {type};
