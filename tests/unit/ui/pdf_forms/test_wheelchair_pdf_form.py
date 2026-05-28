import unittest
from datetime import datetime

import pytz

from common.constants import DeviceType, Location, PaymentMethod, RentalStatus
from common.data_models.rental import NewRental
from ui.pdf_forms.wheelchair_pdf_form import WheelchairPDFForm


class TestWheelchairPDFForm(unittest.TestCase):
    """Test the WheelchairForm class."""

    def test_fill(self):
        """Test the fill_form method."""

        # create fake rental data
        # pylint: disable=no-value-for-parameter
        rental_data = NewRental(
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
        form = WheelchairPDFForm(rental_data=rental_data, rental_id="W0101001")
        pdf_bytes = form.export_form_to_bytes()
        with open("test_wheelchair_form.pdf", "wb") as f:
            f.write(pdf_bytes)
