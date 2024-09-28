WITH check_prequesities
         AS (SELECT check_new_rental_prerequisites({device_id}, {reservation_id})),
     new_rental_id
         AS (SELECT {device_type_prefix} || to_char({date}, 'MMDD') ||
                    (select lpad((1 + count(id))::text, 3, '0')) AS rental_id
             FROM {schema}.{table}
             WHERE date = {date})

INSERT
INTO {schema}.{table} (id, date, device_type, device_id, pickup_location, pickup_time, name, address, city,
                       province, postal_code, country, phone_number, fee_payment_method, fee_payment_amount,
                       deposit_payment_method, deposit_payment_amount, staff_name, items_left_behind, notes, signature)
VALUES ((SELECT rental_id FROM new_rental_id),
        {date},
        {device_type},
        {device_id},
        {pickup_location},
        {pickup_time},
        {name},
        {address},
        {city},
        {province},
        {postal_code},
        {country},
        {phone_number},
        {fee_payment_method},
        {fee_payment_amount},
        {deposit_payment_method},
        {deposit_payment_amount},
        {staff_name},
        {items_left_behind},
        {notes},
        {signature})
RETURNING (SELECT rental_id FROM new_rental_id)
