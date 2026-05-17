from datetime import time
from unittest import TestCase

from streamlit.testing.v1 import AppTest

from common.constants import WALK_IN_RESERVATION_ID
from ui.src.constants import CNEDates


class TestRentalForm(TestCase):
    """Test the rental form"""

    def setUp(self):
        self.mock_prefix = "test_form"

    # pylint: disable=import-outside-toplevel
    @staticmethod
    def _run_form(key_prefix: str, render: bool):
        """Run the form rendering"""
        from ui.forms.new_rental_form import NewRentalForm

        form = NewRentalForm(key_prefix=key_prefix)
        form.initialize_form()
        if render:
            form.render_form()

    def _render_form_and_select_location_device(self):
        """Render the form and select a location and device type"""
        at = AppTest.from_function(self._run_form, args=(self.mock_prefix, True)).run()
        at.time_input(f"{self.mock_prefix}_time").set_value(time(hour=10, minute=30))
        at.selectbox(f"{self.mock_prefix}_pickup_location").select_index(0)
        at.selectbox(f"{self.mock_prefix}_device_type").select_index(0)
        at.run()
        return at

    def test_initialize_form(self):
        """Test that the form is initialized with the correct default values"""

        at = AppTest.from_function(self._run_form, args=(self.mock_prefix, False)).run()
        self.assertEqual(at.session_state[f"{self.mock_prefix}_date"], CNEDates.get_default_date())
        self.assertIsNone(at.session_state[f"{self.mock_prefix}_time"])

        for field, value in {
            "pickup_location": None,
            "device_type": None,
            "reservation_id": None,
            "device_id": None,
            "name": None,
            "phone_number": None,
            "address": None,
            "city": None,
            "province": "Ontario",
            "postal_code": None,
            "country": "Canada",
            "fee_payment_method": None,
            "deposit_payment_method": None,
            "staff_name": None,
        }.items():
            self.assertEqual(at.session_state[f"{self.mock_prefix}_{field}"], value)

    def test_render_form(self):
        """Test that the form is rendered with the correct fields"""
        # check that only the first few fields exist
        at = AppTest.from_function(self._run_form, args=(self.mock_prefix, True)).run()

        with self.subTest("Initial render of form"):
            # only these four fields should be available
            _ = at.date_input(f"{self.mock_prefix}_date")
            _ = at.time_input(f"{self.mock_prefix}_time")
            _ = at.selectbox(f"{self.mock_prefix}_pickup_location")
            _ = at.selectbox(f"{self.mock_prefix}_device_type")

            # these fields should not yet be available (only testing a subset for brevity)
            for field in ["reservation_id", "device_id", "fee_payment_method", "deposit_payment_method"]:
                with self.assertRaises(KeyError):
                    at.selectbox(f"{self.mock_prefix}_{field}")

        # pick a location and device type to render next part of form
        at.time_input(f"{self.mock_prefix}_time").set_value(time(hour=10, minute=30))
        at.selectbox(f"{self.mock_prefix}_pickup_location").select_index(0)
        at.selectbox(f"{self.mock_prefix}_device_type").select_index(0)
        at.run()

        with self.subTest("After selecting pickup location and device type"):
            # these fields should continue to be available
            _ = at.date_input(f"{self.mock_prefix}_date")
            _ = at.time_input(f"{self.mock_prefix}_time")
            _ = at.selectbox(f"{self.mock_prefix}_pickup_location")
            _ = at.selectbox(f"{self.mock_prefix}_device_type")

            # these fields should now also be available
            _ = at.selectbox(f"{self.mock_prefix}_reservation_id")
            _ = at.selectbox(f"{self.mock_prefix}_device_id")

            # these fields should still not be available
            for field in ["fee_payment_method", "deposit_payment_method"]:
                with self.assertRaises(KeyError):
                    at.selectbox(f"{self.mock_prefix}_{field}")

        # add device options
        at.session_state[f"{self.mock_prefix}_available_devices"] = ["W1", "W2", "W3"]
        at.run()

        with self.subTest("After adding available device options"):
            # all of these fields should now be available
            for field in ["pickup_location", "device_type", "reservation_id", "device_id", "fee_payment_method"]:
                _ = at.selectbox(f"{self.mock_prefix}_{field}")

    def test_render_form_device_options(self):
        """Test that the device ID options are updated when the available devices are updated"""
        at = self._render_form_and_select_location_device()
        self.assertEqual(at.selectbox(f"{self.mock_prefix}_device_id").options, [])

        at.session_state[f"{self.mock_prefix}_available_devices"] = ["W1", "W2", "W3"]
        at.run()
        self.assertEqual(at.selectbox(f"{self.mock_prefix}_device_id").options, ["W1", "W2", "W3"])

    def test_render_form_reservation_options(self):
        """Test that the reservation options are updated when the date and device type are updated"""

        at = self._render_form_and_select_location_device()
        self.assertEqual(at.selectbox(f"{self.mock_prefix}_reservation_id").options, [WALK_IN_RESERVATION_ID])

        at.session_state[f"{self.mock_prefix}_reservations"] = ["R1", "R2", "R3"]
        at.run()
        self.assertEqual(
            at.selectbox(f"{self.mock_prefix}_reservation_id").options,
            ["R1", "R2", "R3", WALK_IN_RESERVATION_ID]
        )

    def test_render_form_fee_deposit_amount(self):
        """Test that the fee/deposit amount is updated when the device type is updated"""

        for field in ["fee", "deposit"]:
            with self.subTest(msg=f"Test {field} amount"):
                at = self._render_form_and_select_location_device()
                at.session_state[f"{self.mock_prefix}_available_devices"] = ["W1", "W2", "W3"]
                at.run()
                self.assertEqual(
                    at.selectbox(f"{self.mock_prefix}_{field}_payment_method").label,
                    f"Payment Type for **$0** {field.title()}"
                )

                at.session_state[f"{self.mock_prefix}_{field}_payment_amount"] = 100
                at.run()
                self.assertEqual(
                    at.selectbox(f"{self.mock_prefix}_{field}_payment_method").label,
                    f"Payment Type for **$100** {field.title()}"
                )

    # pylint: disable=import-outside-toplevel,protected-access
    def test_extract_reservation_id(self):
        """Test that the reservation ID is extracted correctly from the reservation name"""
        from ui.forms.new_rental_form import NewRentalForm

        form = NewRentalForm(key_prefix="mock_prefix")

        # normal reservation ID
        result = form._extract_reservation_id("Reservation Name (W0819123)")
        self.assertEqual(result, "W0819123")

        # name with no ID
        result = form._extract_reservation_id("Reservation Name")
        self.assertIsNone(result)

        # name that contains brackets
        result = form._extract_reservation_id("Reservation Name (Extra) (W0819123)")
        self.assertEqual(result, "W0819123")

        # name that contains random characters
        result = form._extract_reservation_id("Reservation !@# Name (12345) (W0819123)")
        self.assertEqual(result, "W0819123")

        # walk-in
        result = form._extract_reservation_id(WALK_IN_RESERVATION_ID)
        self.assertEqual(result, WALK_IN_RESERVATION_ID)
