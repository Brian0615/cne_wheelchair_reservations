SELECT COUNT(DISTINCT id) AS number_of_reservations
FROM {schema}.{table}
WHERE date = {date}
  AND device_type = {device_type}
  AND location = {location}