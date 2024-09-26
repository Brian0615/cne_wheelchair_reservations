INSERT INTO {schema}.{table} (id, type, status, location)
VALUES ({id}, {type}, {status}, {location})
ON CONFLICT (id)
    DO UPDATE SET type     = EXCLUDED.type,
                  status   = EXCLUDED.status,
                  location = EXCLUDED.location;