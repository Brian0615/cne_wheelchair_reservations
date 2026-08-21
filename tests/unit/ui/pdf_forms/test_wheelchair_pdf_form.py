import unittest
from datetime import datetime

import pymupdf
import pytz

from common.constants import DeviceType, Location, PaymentMethod, RentalStatus
from common.data_models.rental import NewRental
from ui.pdf_forms.wheelchair_pdf_form import WheelchairPDFForm


class TestWheelchairPDFForm(unittest.TestCase):
    """Test the WheelchairForm class."""

    def setUp(self):
        # pylint: disable=no-value-for-parameter
        self.rental_data = NewRental(
            cne_year=2021,
            date=datetime(2021, 8, 1),
            name="John Doe",
            phone_number="416-937-2830",
            device_type=DeviceType.WHEELCHAIR,
            device_id="W12",
            pickup_location=Location.BLC,
            pickup_time=pytz.UTC.localize(datetime(2021, 8, 1, 12, 0)),
            status=RentalStatus.IN_PROGRESS,
            address="123 Fake St",
            city="Toronto",
            province="Ontario",
            postal_code="A1B 2C3",
            country="Canada",
            fee_payment_amount=20,
            fee_payment_method=PaymentMethod.CREDIT_CARD,
            deposit_payment_amount=100,
            deposit_payment_method=PaymentMethod.CASH,
            staff_name="Jane Doe",
        )
        self.form = WheelchairPDFForm(rental_data=self.rental_data, rental_id="W0101001")

    def test_fill(self):
        """Test the fill_form method."""
        pdf_bytes = self.form.export_form_to_bytes()
        with open("test_wheelchair_form.pdf", "wb") as f:
            f.write(pdf_bytes)

    def test_fee_and_deposit_come_from_the_rental(self):
        """Both the rental copy and the receipt copy show the recorded amounts."""
        field_values = self.form._create_form_field_values()  # pylint: disable=protected-access
        self.assertEqual(field_values["fee"], "20")
        self.assertEqual(field_values["fee_receipt"], "20")
        self.assertEqual(field_values["deposit"], "100")
        self.assertEqual(field_values["deposit_receipt"], "100")

    def test_every_filled_field_exists_in_the_pdf(self):
        """Guard against the form class and the fillable PDF drifting apart."""
        field_values = self.form._create_form_field_values()  # pylint: disable=protected-access
        with pymupdf.open(WheelchairPDFForm._FILLABLE_FORM_PATH) as pdf:  # pylint: disable=protected-access
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

        for field_name in [
            "id_verified",
            "fee_payment_method_credit_card", "fee_payment_method_receipt_credit_card",
            "deposit_payment_method_cash", "deposit_payment_method_receipt_cash",
        ]:
            self.assertEqual("Yes", widget_values[field_name], f"{field_name} should be checked")
        for field_name in [
            "fee_payment_method_cash", "fee_payment_method_debit_card",
            "deposit_payment_method_credit_card",
        ]:
            self.assertEqual("Off", widget_values[field_name], f"{field_name} should not be checked")
