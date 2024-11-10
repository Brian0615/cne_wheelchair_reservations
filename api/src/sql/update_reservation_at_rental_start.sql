WITH check_reservation AS (SELECT {schema}.check_if_reservation_exists({reservation_id}))

UPDATE {schema}.{table}
SET rental_id = {rental_id},
    status = 'Picked Up'::reservation_status
WHERE id = {reservation_id}
