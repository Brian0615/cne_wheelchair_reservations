SELECT id,
       date,
       name,
       phone_number,
       device_type,
       device_id,
       pickup_location,
       pickup_time,
       deposit_payment_method,
       return_location,
       return_time,
       items_left_behind,
       notes
FROM {schema}.{table}
WHERE date = {date}
  AND ({device_type}::text is null or device_type = {device_type})
  AND ({in_progress_only}::boolean IS FALSE OR return_time IS NULL)
