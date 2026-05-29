from datetime import date, datetime
from unittest import TestCase

import pandas as pd
from pydantic import ValidationError

from common.constants import DeviceType, Location, PaymentMethod, RentalStatus
from common.data_models.rental import CompletedRental, NewRental, RentalSummary
from common.utils import get_default_timezone

_TZ = get_default_timezone()
_DATE = date(2025, 8, 20)
_PICKUP_TIME = _TZ.localize(datetime(2025, 8, 20, 11, 0))
_RETURN_TIME = _TZ.localize(datetime(2025, 8, 20, 16, 0))

_BASE_NEW_RENTAL = {
    "cne_year": 2025,
    "date": _DATE,
    "device_id": "W01",
    "device_type": DeviceType.WHEELCHAIR,
    "reservation_id": None,
    "pickup_location": Location.BLC,
    "pickup_time": _PICKUP_TIME,
    "status": RentalStatus.IN_PROGRESS,
    "name": "John Doe",
    "phone_number": "4168202370",
    "address": "123 Test St",
    "city": "Toronto",
    "province": "Ontario",
    "postal_code": "M5G2C3",
    "country": "Canada",
    "fee_payment_amount": 20,
    "fee_payment_method": PaymentMethod.CASH,
    "deposit_payment_amount": 50,
    "deposit_payment_method": PaymentMethod.CASH,
    "items_left_behind": [],
    "notes": None,
    "staff_name": "Staff One",
    "return_location": None,
    "return_time": None,
    "return_staff_name": None,
}


class TestNewRental(TestCase):
    """Tests for the NewRental data model."""

    def test_valid_wheelchair_rental(self):
        rental = NewRental(**_BASE_NEW_RENTAL)
        self.assertEqual("W01", rental.device_id)
        self.assertEqual(DeviceType.WHEELCHAIR, rental.device_type)

    def test_valid_scooter_rental(self):
        params = {**_BASE_NEW_RENTAL, "device_id": "S01", "device_type": DeviceType.SCOOTER,
                  "reservation_id": None, "fee_payment_amount": 45, "deposit_payment_amount": 100}
        rental = NewRental(**params)
        self.assertEqual("S01", rental.device_id)

    def test_device_id_type_mismatch_raises(self):
        with self.assertRaises(ValidationError):
            NewRental(**{**_BASE_NEW_RENTAL, "device_id": "S01", "device_type": DeviceType.WHEELCHAIR})

    def test_reservation_id_type_mismatch_raises(self):
        with self.assertRaises(ValidationError):
            NewRental(**{**_BASE_NEW_RENTAL, "reservation_id": "S0820001"})

    def test_postal_code_validated_for_canada(self):
        """An invalid Canadian postal code format raises a ValidationError."""
        with self.assertRaises(ValidationError):
            NewRental(**{**_BASE_NEW_RENTAL, "postal_code": "INVALID"})

    def test_province_normalised_for_canada(self):
        """Province name is normalised to a subdivision code for Canadian addresses."""
        rental = NewRental(**{**_BASE_NEW_RENTAL, "province": "Ontario"})
        self.assertEqual("ON", rental.province)

    def test_country_code_normalised(self):
        rental = NewRental(**{**_BASE_NEW_RENTAL, "country": "Canada"})
        self.assertEqual("CAN", str(rental.country))

    def test_cne_year_and_date_consistent(self):
        with self.assertRaises(ValidationError):
            NewRental(**{**_BASE_NEW_RENTAL, "date": date(2024, 8, 20)})

    def test_extra_fields_forbidden(self):
        with self.assertRaises(ValidationError):
            NewRental(**{**_BASE_NEW_RENTAL, "unexpected_field": "value"})

    def test_us_rental_with_state(self):
        """US address with a valid state is accepted."""
        params = {
            **_BASE_NEW_RENTAL,
            "country": "USA",
            "province": "New York",
            "postal_code": "10001",
        }
        rental = NewRental(**params)
        self.assertEqual("NY", rental.province)


class TestCompletedRental(TestCase):
    """Tests for the CompletedRental data model."""

    _BASE = {
        "cne_year": 2025,
        "id": "W0820001",
        "date": _DATE,
        "device_id": "W01",
        "reservation_id": None,
        "name": "John Doe",
        "return_location": Location.BLC,
        "return_time": _RETURN_TIME,
        "return_staff_name": "Staff One",
    }

    def test_valid_completed_rental(self):
        rental = CompletedRental(**self._BASE)
        self.assertEqual("W0820001", rental.id)
        self.assertEqual("W01", rental.device_id)

    def test_extra_fields_forbidden(self):
        with self.assertRaises(ValidationError):
            CompletedRental(**{**self._BASE, "status": "Completed"})

    def test_cne_year_and_date_consistent(self):
        with self.assertRaises(ValidationError):
            CompletedRental(**{**self._BASE, "date": date(2024, 8, 20)})


class TestRentalSummary(TestCase):
    """Tests for the RentalSummary data model."""

    _BASE = {
        "cne_year": 2025,
        "id": "W0820001",
        "date": _DATE,
        "device_id": "W01",
        "device_type": DeviceType.WHEELCHAIR,
        "reservation_id": None,
        "pickup_location": Location.BLC,
        "pickup_time": _PICKUP_TIME,
        "status": RentalStatus.IN_PROGRESS,
        "name": "John Doe",
        "phone_number": "4168202370",
        "deposit_payment_method": PaymentMethod.CASH,
        "items_left_behind": [],
        "notes": None,
        "return_location": None,
        "return_time": None,
    }

    def test_valid_rental_summary(self):
        summary = RentalSummary(**self._BASE)
        self.assertEqual("W0820001", summary.id)

    def test_nat_return_time_converted_to_none(self):
        summary = RentalSummary(**{**self._BASE, "return_time": pd.NaT})
        self.assertIsNone(summary.return_time)

    def test_device_id_type_mismatch_raises(self):
        with self.assertRaises(ValidationError):
            RentalSummary(**{**self._BASE, "device_id": "S01", "device_type": DeviceType.WHEELCHAIR})
