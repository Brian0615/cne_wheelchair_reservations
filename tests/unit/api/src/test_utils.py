from unittest import TestCase

from fastapi import HTTPException

from api.src.exceptions import (
    DeviceNotFoundException,
    DeviceNotFoundOrInvalidStatusException,
    NewReservationNotFoundOrNotEditableException,
    RentalNotFoundOrNotEditableException,
    ReservationNotFoundOrNotEditableException,
)
from api.src.utils import auto_process_database_errors


class TestAutoProcessDatabaseErrors(TestCase):
    """Tests for the auto_process_database_errors decorator."""

    def test_returns_result_when_no_exception(self):
        @auto_process_database_errors
        def func():
            return "success"

        self.assertEqual("success", func())

    def test_passes_args_and_kwargs(self):
        @auto_process_database_errors
        def func(a, b, c=None):
            return (a, b, c)

        self.assertEqual((1, 2, 3), func(1, 2, c=3))

    def test_device_not_found_raises_404(self):
        @auto_process_database_errors
        def func():
            raise DeviceNotFoundException("Device not found")

        with self.assertRaises(HTTPException) as ctx:
            func()
        self.assertEqual(404, ctx.exception.status_code)
        self.assertIn("Device not found", ctx.exception.detail)

    def test_device_not_found_or_invalid_status_raises_400(self):
        @auto_process_database_errors
        def func():
            raise DeviceNotFoundOrInvalidStatusException(2025, "W01", "Available")

        with self.assertRaises(HTTPException) as ctx:
            func()
        self.assertEqual(400, ctx.exception.status_code)

    def test_rental_not_found_or_not_editable_raises_400(self):
        @auto_process_database_errors
        def func():
            raise RentalNotFoundOrNotEditableException(2025, "W0820001")

        with self.assertRaises(HTTPException) as ctx:
            func()
        self.assertEqual(400, ctx.exception.status_code)

    def test_reservation_not_found_or_not_editable_raises_400(self):
        @auto_process_database_errors
        def func():
            raise ReservationNotFoundOrNotEditableException("Reservation not editable")

        with self.assertRaises(HTTPException) as ctx:
            func()
        self.assertEqual(400, ctx.exception.status_code)

    def test_new_reservation_not_found_or_not_editable_raises_400(self):
        @auto_process_database_errors
        def func():
            raise NewReservationNotFoundOrNotEditableException(2025, "S0820001")

        with self.assertRaises(HTTPException) as ctx:
            func()
        self.assertEqual(400, ctx.exception.status_code)

    def test_unrelated_exception_propagates(self):
        @auto_process_database_errors
        def func():
            raise ValueError("unrelated error")

        with self.assertRaises(ValueError):
            func()
