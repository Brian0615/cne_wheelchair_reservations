UPDATE {schema}.{table}
SET status = 'Completed'::wheelchairs.reservation_status
WHERE rental_id = {rental_id}
