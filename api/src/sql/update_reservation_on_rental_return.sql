UPDATE {schema}.{table}
SET status = 'Completed'::reservation_status
WHERE rental_id = {rental_id}
