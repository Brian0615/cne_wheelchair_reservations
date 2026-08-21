import unittest
from datetime import datetime

import pymupdf
import pytz

from common.constants import DeviceType, Location, PaymentMethod, RentalStatus
from common.data_models.rental import NewRental
from ui.pdf_forms.scooter_pdf_form import ScooterPDFForm


class TestScooterPDFForm(unittest.TestCase):
    """Test the ScooterPDFForm class."""

    def setUp(self):
        # pylint: disable=no-value-for-parameter
        self.rental_data = NewRental(
            cne_year=2021,
            date=datetime(2021, 8, 1),
            name="John Doe",
            phone_number="416-937-2830",
            device_type=DeviceType.SCOOTER,
            device_id="S12",
            pickup_location=Location.BLC,
            pickup_time=pytz.UTC.localize(datetime(2021, 8, 1, 12, 0)),
            status=RentalStatus.IN_PROGRESS,
            address="123 Fake St",
            city="Toronto",
            province="Ontario",
            postal_code="A1B 2C3",
            country="Canada",
            fee_payment_amount=45,
            fee_payment_method=PaymentMethod.CASH,
            deposit_payment_amount=100,
            deposit_payment_method=PaymentMethod.CREDIT_CARD,
            staff_name="Jane Doe",
        )
        self.form = ScooterPDFForm(rental_data=self.rental_data, rental_id="S0101001")

    def test_fill(self):
        """Test the fill_form method."""
        pdf_bytes = self.form.export_form_to_bytes()
        with open("test_scooter_form.pdf", "wb") as f:
            f.write(pdf_bytes)

    def test_fee_and_deposit_come_from_the_rental(self):
        """The fee and deposit amounts should be the ones recorded on the rental."""
        field_values = self.form._create_form_field_values()  # pylint: disable=protected-access
        self.assertEqual(field_values["fee"], "45.00")
        self.assertEqual(field_values["fee_summary"], "45")
        self.assertEqual(field_values["deposit"], "100.00")
        self.assertEqual(field_values["deposit_summary"], "100")

    def test_date_is_split_into_day_month_and_year(self):
        """The agreement's "Dated this ..." line is filled from the rental date."""
        field_values = self.form._create_form_field_values()  # pylint: disable=protected-access
        self.assertEqual(field_values["date_day"], "1st")
        self.assertEqual(field_values["date_month"], "August")
        self.assertEqual(field_values["date_year"], "2021")

    def test_every_filled_field_exists_in_the_pdf(self):
        """Guard against the form class and the fillable PDF drifting apart."""
        field_values = self.form._create_form_field_values()  # pylint: disable=protected-access
        with pymupdf.open(ScooterPDFForm._FILLABLE_FORM_PATH) as pdf:  # pylint: disable=protected-access
            widget_names = {widget.field_name for widget in pdf[0].widgets()}
        self.assertEqual(set(field_values) - widget_names, set())

    def test_checkboxes_are_actually_checked_in_the_exported_pdf(self):
        """Regression test: checkbox fields (ID verified, fee/deposit payment method) must render
        as checked in the exported PDF, not just carry a truthy-looking value in Python. PyMuPDF
        only checks a box when the assigned value matches its export state exactly ("Yes" here) --
        an unrecognized value like the string "yes" silently leaves the box unchecked."""
        pdf_bytes = self.form.export_form_to_bytes()
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
            widget_values = {widget.field_name: widget.field_value for widget in pdf[0].widgets()}

        for field_name in ["id_verified", "fee_payment_method_cash", "deposit_payment_method_credit_card"]:
            self.assertEqual(widget_values[field_name], "Yes", f"{field_name} should be checked")
        for field_name in [
            "fee_payment_method_credit_card", "fee_payment_method_debit_card", "deposit_payment_method_cash",
        ]:
            self.assertEqual(widget_values[field_name], "Off", f"{field_name} should not be checked")
