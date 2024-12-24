WITH check_reservation AS (SELECT {schema}.check_if_device_available({device_id}))

UPDATE {schema}.{table}
SET status = 'Available'::device_status
WHERE id = {device_id}
