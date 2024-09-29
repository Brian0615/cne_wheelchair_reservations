WITH new_reservation_id
         AS (SELECT {device_type_prefix} || to_char({date}, 'MMDD') ||
                    (select lpad((1 + count(id))::text, 3, '0')) AS reservation_id
             FROM {schema}.{table}
             WHERE date = {date})

INSERT
INTO {schema}.{table} (id, date, device_type, name, phone_number, location, reservation_time, status)
VALUES ((SELECT reservation_id FROM new_reservation_id),
        {date},
        {device_type},
        {name},
        {phone_number},
        {location},
        {reservation_time},
        {status})
RETURNING (SELECT reservation_id FROM new_reservation_id)