WITH check_rental AS (SELECT {schema}.check_if_rental_exists({rental_id}))

UPDATE {schema}.{table}
SET return_location   = {return_location},
    return_time       = {return_time},
    return_staff_name = {return_staff_name},
    return_signature  = {return_signature}
WHERE id = {rental_id}
