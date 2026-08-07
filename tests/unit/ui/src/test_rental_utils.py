# pylint: disable=missing-class-docstring,missing-function-docstring

from datetime import date, datetime, time
from unittest import TestCase
from unittest.mock import patch

import pandas as pd
import pymupdf

from common.constants import DeviceType, Location, PaymentMethod
from common.data_models import CompletedRental
from common.utils import get_default_timezone
from common.cne_dates import CNEDates
from ui.src.data_service import DataService
from ui.src.rental_utils import export_late_returns_to_pdf, submit_complete_rental_form


class TestRentalUtils(TestCase):

    def setUp(self):
        pass

    @patch.object(CNEDates, attribute="get_cne_year", return_value=2024)
    @patch.object(DataService, attribute="complete_rental", return_value=(200, None))
    @patch("ui.src.rental_utils.display_complete_rental_success_dialog")
    def test_submit_complete_rental_form(self, mock_complete_rental, mock_success_dialog, _):
        mock_completed_rental = {
            "date": date(2024, 9, 1),
            "id": "W0901001",
            "name": "John Doe",
            "device_id": "W04",
            "return_date": date(2024, 9, 1),
            "return_time": time(15, 30),
            "return_location": Location.PG,
            "return_staff_name": "Test Staff",
        }
        expected_called_with = CompletedRental(
            cne_year=2024,
            date=date(2024, 9, 1),
            id="W0901001",
            name="John Doe",
            device_id="W04",
            return_time=get_default_timezone().localize(datetime(2024, 9, 1, 15, 30)),
            return_location=Location.PG,
            return_staff_name="Test Staff",
        )

        submit_complete_rental_form(mock_completed_rental)
        mock_complete_rental.assert_called_once_with(expected_called_with)
        mock_success_dialog.assert_called_once()


class TestExportLateReturnsToPdf(TestCase):

    def setUp(self):
        self.rentals_df = pd.DataFrame([
            {
                "id": "W0901001",
                "name": "John Doe",
                "phone_number": "tel:+1 416-555-1234",
                "device_id": "W01",
                "device_type": DeviceType.WHEELCHAIR,
                "pickup_location": Location.BLC,
                "deposit_payment_method": PaymentMethod.CASH,
                "deposit_payment_amount": 50,
                "items_left_behind": ["Walker"],
                "return_time": None,
            },
            {
                "id": "S0901001",
                "name": "Alice Green",
                "phone_number": "416-555-9999",
                "device_id": "S01",
                "device_type": DeviceType.SCOOTER,
                "pickup_location": Location.PG,
                "deposit_payment_method": PaymentMethod.CASH,
                "deposit_payment_amount": 100,
                "items_left_behind": [],
                "return_time": None,
            },
            {
                "id": "W0901002",
                "name": "Jane Smith",
                "phone_number": "416-555-6789",
                "device_id": "W02",
                "device_type": DeviceType.WHEELCHAIR,
                "pickup_location": Location.PG,
                "deposit_payment_method": PaymentMethod.CREDIT_CARD,
                "deposit_payment_amount": 50,
                "items_left_behind": [],
                "return_time": pd.Timestamp("2025-09-01T15:00:00-04:00"),
            },
        ])

    @staticmethod
    def _extract_text(pdf_bytes: bytes) -> str:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
            return "".join(page.get_text() for page in pdf)

    def test_only_unreturned_rentals_are_included(self):
        text = self._extract_text(export_late_returns_to_pdf(self.rentals_df.copy(), date(2025, 9, 1)))
        self.assertIn("W0901001", text)
        self.assertNotIn("W0901002", text)

    def test_pdf_includes_required_columns_and_signature_lines(self):
        text = self._extract_text(export_late_returns_to_pdf(self.rentals_df.copy(), date(2025, 9, 1)))
        self.assertIn("John Doe", text)
        self.assertIn("+1 416-555-1234", text)  # tel: prefix stripped
        self.assertIn("W01", text)
        self.assertIn("$50", text)
        self.assertIn("Walker", text)
        self.assertIn("Issued by", text)
        self.assertIn("Received by", text)
        # renamed headers
        self.assertIn("Name", text)
        self.assertIn("Phone Number", text)
        self.assertIn("Location", text)
        self.assertIn("Notes", text)
        self.assertNotIn("Renter Name", text)
        self.assertNotIn("Renter Phone Number", text)
        self.assertNotIn("Pickup Location", text)
        self.assertNotIn("Items Left Behind", text)

    def test_scooters_and_wheelchairs_are_in_separate_tables(self):
        text = self._extract_text(export_late_returns_to_pdf(self.rentals_df.copy(), date(2025, 9, 1)))
        self.assertIn("Wheelchair Late Returns", text)
        self.assertIn("Scooter Late Returns", text)
        self.assertIn("Wheelchair", text)
        self.assertIn("Scooter", text)
        self.assertNotIn("Device ID", text)
        # the scooter section should appear before the wheelchair one, and each rental
        # should only appear once, under its own device type's table
        self.assertLess(text.index("S0901001"), text.index("Wheelchair Late Returns"))
        self.assertGreater(text.index("W0901001"), text.index("Wheelchair Late Returns"))

    def test_no_late_returns_shows_message(self):
        all_returned = self.rentals_df[self.rentals_df["return_time"].notna()].copy()
        text = self._extract_text(export_late_returns_to_pdf(all_returned, date(2025, 9, 1)))
        self.assertIn("There are no late returns.", text)

    def test_long_name_and_notes_are_wrapped(self):
        long_name_df = pd.DataFrame([{
            "id": "W0901003",
            "name": "Alexandria Montgomery-Fitzgerald",
            "phone_number": "416-555-0000",
            "device_id": "W03",
            "device_type": DeviceType.WHEELCHAIR,
            "pickup_location": Location.BLC,
            "deposit_payment_method": PaymentMethod.CASH,
            "deposit_payment_amount": 50,
            "items_left_behind": ["Walker", "Stroller", "Blanket", "Umbrella"],
            "return_time": None,
        }])
        text = self._extract_text(export_late_returns_to_pdf(long_name_df, date(2025, 9, 1)))
        # the full name/notes should not appear on a single line; wrapping breaks them up
        self.assertNotIn("Alexandria Montgomery-Fitzgerald", text)
        self.assertIn("Alexandria", text)
        self.assertNotIn("Walker, Stroller, Blanket, Umbrella", text)
        self.assertIn("Walker", text)
