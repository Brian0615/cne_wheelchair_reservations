CREATE TYPE device_status AS ENUM (
    'Available',
    'Backup',
    'Out of Order',
    'Rented',
    'Out of Service'
    );

CREATE TYPE device_type AS ENUM (
    'Scooter',
    'Wheelchair'
    );

CREATE TYPE hold_item AS ENUM (
    'Cane',
    'Crutches',
    'Stroller',
    'Walker',
    'Wheelchair',
    'Other'
    );

CREATE TYPE location AS ENUM (
    'BLC',
    'PG'
    );

CREATE TYPE payment_method AS ENUM (
    'Cash',
    'Credit Card',
    'Debit Card'
    );

CREATE TYPE reservation_status AS ENUM (
    'Pending Confirmation',
    'Confirmed',
    'Reserved',
    'Picked Up',
    'Completed',
    'Cancelled'
    );