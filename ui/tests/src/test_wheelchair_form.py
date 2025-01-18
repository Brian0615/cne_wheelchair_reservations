import os
import unittest
from datetime import datetime

import pytz
from PIL import Image

from common.constants import PaymentMethod, DeviceType, Location
from common.data_models.rental import NewRental
from ui.src.utils import encode_signature_base64
from ui.src.wheelchair_form import WheelchairForm


class TestWheelchairForm(unittest.TestCase):
    """Test the WheelchairForm class."""

    def test_fill(self):
        """Test the fill_form method with a signature."""

        # load test signature
        signature = Image.open(os.path.join(os.path.dirname(__file__), "assets/test_signature.png"))

        # create fake rental data
        rental_data = NewRental(
            date=datetime(2021, 8, 1),
            name="John Doe",
            phone_number="123-456-789",
            device_type=DeviceType.WHEELCHAIR,
            device_id="W123",
            pickup_location=Location.BLC,
            pickup_time=datetime(2021, 8, 1, 12, 0, tzinfo=pytz.UTC),
            address="123 Fake St",
            city="Toronto",
            province="Ontario",
            postal_code="A1B 2C3",
            country="Canada",
            fee_payment_amount=50,
            fee_payment_method=PaymentMethod.CASH,
            deposit_payment_amount=100,
            deposit_payment_method=PaymentMethod.CREDIT_CARD,
            staff_name="Jane Doe",
            signature=encode_signature_base64(signature),
        )

        WheelchairForm.fill_form(rental_data, "test_rental_id")
