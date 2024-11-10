CREATE OR REPLACE FUNCTION {schema}.raise_custom_error(p_error_code TEXT, details TEXT DEFAULT NULL)
    RETURNS VOID AS
$$
DECLARE
    v_error_message TEXT;
BEGIN
    -- Find error message in the custom_error_messages table
    SELECT error_message::text
    INTO v_error_message
    FROM {schema}.{custom_exceptions_table}
    WHERE error_code = p_error_code;

    IF details IS NOT NULL THEN
        v_error_message := v_error_message || ' (' || details || ')';
    END IF;

    -- Raise exception with the retrieved error message
    RAISE EXCEPTION USING
        ERRCODE = p_error_code,
        MESSAGE = v_error_message;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION {schema}.check_if_device_available(device_id TEXT)
    RETURNS VOID AS
$$
DECLARE
    device_status TEXT;
BEGIN
    -- Check the status of the device
    SELECT status
    INTO device_status
    FROM {schema}.{devices_table}
    WHERE id = device_id;

    -- if device doesn't exist, raise error
    IF device_status IS NULL THEN
        PERFORM {schema}.raise_custom_error(p_error_code := 'E1001', details := device_id);
    ELSIF device_status::device_status = 'Rented'::device_status THEN
        PERFORM {schema}.raise_custom_error(p_error_code := 'E1002', details := device_id);
    ELSIF device_status::device_status = 'Out of Service'::device_status THEN
        PERFORM {schema}.raise_custom_error(p_error_code := 'E1003', details := device_id);
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION {schema}.check_if_rental_exists(rental_id TEXT)
    RETURNS VOID AS
$$
DECLARE
    rental_status TEXT;
BEGIN
    -- Check the status of the rental
    SELECT status
    INTO rental_status
    FROM {schema}.{rentals_table}
    WHERE id = rental_id;

    -- if rental doesn't exist, raise error
    IF rental_status IS NULL THEN
        PERFORM {schema}.raise_custom_error(p_error_code := 'E3001', details := rental_id);
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION {schema}.check_if_reservation_exists(reservation_id TEXT)
    RETURNS VOID AS
$$
DECLARE
    reservation_status TEXT;
BEGIN
    -- Check the status of the reservation
    SELECT status
    INTO reservation_status
    FROM {schema}.{reservations_table}
    WHERE id = reservation_id;

    -- return result
    -- if reservation doesn't exist, raise error
    IF reservation_status IS NULL THEN
        PERFORM {schema}.raise_custom_error(p_error_code := 'E2001', details := reservation_id);
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION {schema}.check_new_rental_prerequisites(device_id TEXT, reservation_id TEXT)
    RETURNS VOID AS
$$
BEGIN
    PERFORM {schema}.check_if_device_available(device_id);

    IF reservation_id::text IS NOT NULL THEN
        PERFORM {schema}.check_if_reservation_exists(reservation_id);
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION {schema}.check_if_device_exists(device_id TEXT)
    RETURNS VOID AS
$$
DECLARE
    device_id_exists BOOLEAN;
BEGIN
    -- Check if the device exists
    SELECT EXISTS (SELECT 1
                   FROM {schema}.{devices_table}
                   WHERE id = device_id)
    INTO device_id_exists;

    -- if device doesn't exist, raise error
    IF NOT device_id_exists THEN
        PERFORM {schema}.raise_custom_error(p_error_code := 'E1001', details := device_id);
    END IF;
END;
$$ LANGUAGE plpgsql;
