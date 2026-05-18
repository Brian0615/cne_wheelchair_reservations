from datetime import date, datetime
from unittest import TestCase

from pydantic import ValidationError

from common.constants import DeviceType, Location, ReservationStatus
from common.data_models.reservation import NewReservation, Reservation, ReservationCount
from common.utils import get_default_timezone

_TZ = get_default_timezone()
_DATE = date(2025, 8, 20)
_RESERVATION_TIME = _TZ.localize(datetime(2025, 8, 20, 10, 0))

_BASE_RESERVATION = dict(
    cne_year=2025,
    id="S0820001",
    date=_DATE,
    device_type=DeviceType.SCOOTER,
    location=Location.BLC,
    reservation_time=_RESERVATION_TIME,
    name="Alice Smith",
    phone_number="9052938402",
    notes="",
    status=ReservationStatus.RESERVED,
    rental_id=None,
)


class TestReservation(TestCase):
    """Tests for the Reservation data model."""

    def test_valid_reservation(self):
        r = Reservation(**_BASE_RESERVATION)
        self.assertEqual("S0820001", r.id)
        self.assertEqual(DeviceType.SCOOTER, r.device_type)

    def test_id_pattern_enforced(self):
        with self.assertRaises(ValidationError):
            Reservation(**{**_BASE_RESERVATION, "id": "INVALID"})

    def test_name_too_short_raises(self):
        with self.assertRaises(ValidationError):
            Reservation(**{**_BASE_RESERVATION, "name": "Al"})

    def test_invalid_device_type_raises(self):
        with self.assertRaises(ValidationError):
            Reservation(**{**_BASE_RESERVATION, "device_type": "Bicycle"})

    def test_invalid_location_raises(self):
        with self.assertRaises(ValidationError):
            Reservation(**{**_BASE_RESERVATION, "location": "NOWHERE"})

    def test_invalid_status_raises(self):
        with self.assertRaises(ValidationError):
            Reservation(**{**_BASE_RESERVATION, "status": "Unknown"})

    def test_rental_id_pattern_enforced(self):
        with self.assertRaises(ValidationError):
            Reservation(**{**_BASE_RESERVATION, "rental_id": "INVALID_ID"})

    def test_extra_fields_forbidden(self):
        with self.assertRaises(ValidationError):
            Reservation(**{**_BASE_RESERVATION, "extra": "value"})

    def test_notes_defaults_to_na_when_omitted(self):
        params = {k: v for k, v in _BASE_RESERVATION.items() if k != "notes"}
        r = Reservation(**params)
        self.assertEqual("N/A", r.notes)


class TestNewReservation(TestCase):
    """Tests for the NewReservation data model (id is optional)."""

    def test_valid_new_reservation_without_id(self):
        params = {**_BASE_RESERVATION, "id": None}
        r = NewReservation(**params)
        self.assertIsNone(r.id)

    def test_valid_new_reservation_with_id(self):
        r = NewReservation(**_BASE_RESERVATION)
        self.assertEqual("S0820001", r.id)


class TestReservationCount(TestCase):
    """Tests for the ReservationCount data model."""

    _BASE = dict(
        date=_DATE,
        device_type=DeviceType.SCOOTER,
        location=Location.BLC,
        count=5,
    )

    def test_valid_reservation_count(self):
        rc = ReservationCount(**self._BASE)
        self.assertEqual(5, rc.count)

    def test_negative_count_raises(self):
        with self.assertRaises(ValidationError):
            ReservationCount(**{**self._BASE, "count": -1})

    def test_zero_count_allowed(self):
        rc = ReservationCount(**{**self._BASE, "count": 0})
        self.assertEqual(0, rc.count)

    def test_extra_fields_forbidden(self):
        with self.assertRaises(ValidationError):
            ReservationCount(**{**self._BASE, "extra": "value"})
