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
