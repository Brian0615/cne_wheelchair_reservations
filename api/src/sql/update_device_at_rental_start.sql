WITH check_reservation AS (SELECT check_if_device_available({device_id}))

UPDATE {schema}.{table}
SET status = 'Rented'::wheelchairs.device_status
WHERE id = {device_id}
