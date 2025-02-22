WITH check_reservation AS (SELECT {schema}.check_if_reservation_exists({reservation_id}))

UPDATE {schema}.{table}
SET date             = {date},
    device_type      = {device_type},
    location         = {location},
    name             = {name},
    phone_number     = {phone_number},
    reservation_time = {reservation_time},
    notes            = {notes}
WHERE id = {reservation_id}
