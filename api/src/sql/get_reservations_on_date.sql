SELECT id,
       date,
       device_type,
       name,
       phone_number,
       location,
       pickup_time,
       status,
       device_id,
       rental_id,
       notes
FROM {schema}.{table}
WHERE date = {date}
