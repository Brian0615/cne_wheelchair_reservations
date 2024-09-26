WITH reservation_id_table
         AS (SELECT {device_type_prefix} || to_char({date}, 'MMDD') ||
                    (select lpad((1 + count(id))::text, 3, '0')) AS reservation_id
             FROM wheelchairs.reservations
             WHERE date = {date})

INSERT
INTO {schema}.{table} (id, date, type, name, phone_number, location, pickup_time, status)
VALUES ((SELECT reservation_id FROM reservation_id_table),
        {date},
        {device_type},
        {name},
        {phone_number},
        {location},
        {pickup_time},
        {status})
RETURNING (SELECT reservation_id FROM reservation_id_table)