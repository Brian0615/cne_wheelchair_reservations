SELECT id,
       date,
       device_type,
       name,
       phone_number,
       location,
       reservation_time,
       status,
       rental_id,
       notes
FROM {schema}.{table}
WHERE date = {date}
  AND ({device_type}::text is null or device_type = {device_type})
