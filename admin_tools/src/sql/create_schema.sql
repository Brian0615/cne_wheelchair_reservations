CREATE SCHEMA {schema_name}

    CREATE TABLE {devices_table} (
        id       varchar(3)    NOT NULL,
        type     device_type   NOT NULL,
        status   device_status NOT NULL,
        location location      NOT NULL,
        CONSTRAINT devices_pk PRIMARY KEY (id)
    )

    CREATE TABLE {rentals_table} (
        id                     varchar(8)               NOT NULL,
        date                   date                     NOT NULL,
        device_type            device_type              NOT NULL,
        device_id              varchar                  NOT NULL,
        pickup_location        location                 NOT NULL,
        return_location        location,
        name                   varchar                  NOT NULL,
        address                varchar                  NOT NULL,
        city                   varchar                  NOT NULL,
        province               varchar                  NOT NULL,
        postal_code            varchar,
        country                varchar                  NOT NULL,
        phone_number           varchar                  NOT NULL,
        fee_payment_method     payment_method           NOT NULL,
        fee_payment_amount     integer                  NOT NULL,
        deposit_payment_method payment_method           NOT NULL,
        deposit_payment_amount integer                  NOT NULL,
        pickup_time            timestamp with time zone NOT NULL,
        return_time            timestamp with time zone,
        staff_name             varchar                  NOT NULL,
        items_left_behind      hold_item[],
        notes                  varchar,
        signature              bytea                    NOT NULL,
        return_signature       bytea,
        return_staff_name      varchar,
        CONSTRAINT rentals_pk PRIMARY KEY (id)
    )

    CREATE TABLE {reservations_table} (
        id               varchar(8)               NOT NULL,
        device_type      device_type              NOT NULL,
        name             varchar                  NOT NULL,
        phone_number     varchar                  NOT NULL,
        location         location                 NOT NULL,
        rental_id        varchar(8),
        status           reservation_status       NOT NULL,
        date             date,
        notes            varchar,
        reservation_time timestamp with time zone NOT NULL,
        CONSTRAINT reservations_pk PRIMARY KEY (id),
        CONSTRAINT rental_id FOREIGN KEY (rental_id) REFERENCES {rentals_table} (id)
    )

    CREATE TABLE {custom_exceptions_table} (
        error_code    varchar NOT NULL,
        error_message varchar NOT NULL,
        CONSTRAINT custom_exceptions_pk PRIMARY KEY (error_code)
    );
