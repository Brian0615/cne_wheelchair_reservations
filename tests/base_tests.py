import json
import os
import unittest
from typing import List, Optional
from unittest.mock import patch, MagicMock

import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

from common.constants import DeviceType
from common.utils import get_default_timezone
from tests.mock_requests import MockRequests
from ui.src import auth_utils
from ui.src.constants import CNEDates


# pylint: disable=too-few-public-methods
class BaseTestCases:
    """Shared Test Cases"""

    class BaseUIPageTest(unittest.TestCase):
        """Shared Test Cases for UI Pages"""

        def setUp(self):
            self.page_path = None

        @staticmethod
        def _load_mock_data_from_json(device_type: DeviceType, data_type: str):
            """Load mock data from a JSON file"""
            with open(
                    os.path.join(
                        os.path.dirname(__file__),
                        f"ui/ui_pages/data/mock_{device_type.value.lower()}_{data_type}_data.json"
                    ),
                    encoding="utf-8"
            ) as file:
                return json.load(file)

        def test_unauthenticated_user(self):
            """Test if unauthenticated user is redirected to login page."""
            with patch.object(auth_utils, "initialize_authenticator"):
                # mock the switch_page method so we can check whether the user was redirected to login
                st.switch_page = MagicMock()

                at = AppTest.from_file(self.page_path)
                at.run()
                st.switch_page.assert_called_once_with("ui/ui_pages/login.py")

        def init_authenticated_app_test(self):
            """Initialize an AppTest instance assuming the user is already authenticated"""
            st.cache_data.clear()  # clear the cache before starting a new test
            at = AppTest.from_file(self.page_path, default_timeout=1000000)
            at.session_state["authentication_status"] = True
            at.session_state["username"] = "test_user"
            return at

        def _run_app_test_with_mock_requests(
                self,
                mock_requests: MockRequests,
                at: Optional[AppTest] = None,
                allow_errors: bool = False
        ):
            with patch.object(requests, "get", side_effect=mock_requests.mock_requests_get):
                with patch.object(requests, "post", side_effect=mock_requests.mock_requests_post):
                    with patch.object(requests, "put", side_effect=mock_requests.mock_requests_put):
                        with patch.object(auth_utils, "initialize_authenticator"):
                            if at is None:
                                at = self.init_authenticated_app_test()
                            at.run()
            if not allow_errors:
                self.assertEqual(0, len(at.error), f"Error running AppTest: {at.error.values}")
            return at

        def _test_date_input(self, key: str):
            """Test the date input for the provided range and default date"""
            at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())
            date_input = at.date_input(key=key)
            cne_start_date, cne_end_date = CNEDates.get_cne_start_end_dates()
            self.assertEqual(cne_start_date.date(), date_input.min, "The start date should be the CNE start date")
            self.assertEqual(cne_end_date.date(), date_input.max, "The end date should be the CNE end date")
            self.assertEqual(CNEDates.get_default_date(), date_input.value, "The default date should be today")

        def _test_single_device_reservations_or_rentals_only(
                self,
                device_type: DeviceType,
                data_type: str,
                time_cols: List[str],
        ):
            """Check the UI content for when there are only reservations or rentals for a single device type"""
            if data_type not in {"reservations", "rentals"}:
                raise ValueError(f"Unsupported data type: {data_type}")

            data = self._load_mock_data_from_json(device_type=device_type, data_type=data_type)
            mock_requests = MockRequests(
                mock_reservations_data=data if data_type == "reservations" else None,
                mock_rentals_data=data if data_type == "rentals" else None,
            )
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

            # as there are reservations/rentals of one type, the No Reservations/Rentals Today warning should not appear
            self.assertFalse(
                any(f"No {data_type.title()} Today" in warning.value for warning in at.warning),
                f'"No {data_type.title()} Today" should not appear as there are {device_type.value.lower()} {data_type}'
            )

            # the Scooter and Wheelchair Reservations/Rentals subheaders should be displayed
            self.assertEqual(2, len(at.subheader), f"There should be two subheaders for the {data_type}")
            self.assertTrue(
                any(f"{device_type.title()} {data_type.title()}" in subheader.value for subheader in at.subheader),
                f"A subheader should be displayed for {device_type.value.lower()} {data_type}"
            )

            # a warning should be displayed for the device that does NOT have rentals/reservations
            other_device_type = DeviceType.SCOOTER if device_type == DeviceType.WHEELCHAIR else DeviceType.WHEELCHAIR
            self.assertTrue(
                any(f"No {other_device_type.title()} {data_type.title()}" in warning.value for warning in at.warning),
                f"A warning should be displayed for the {other_device_type.value.lower()} {data_type}"
            )

            # one dataframe should be displayed for the reservations/rentals, and times should be in the right timezone
            self.assertEqual(1, len(at.dataframe), f"Missing dataframe for {device_type.value.lower()} {data_type}")
            for time_col in time_cols:
                self.assertEqual(
                    get_default_timezone(), at.dataframe[0].value[time_col].dt.tz,  # pylint: disable=no-member
                    f"The {time_col} column should be in the default timezone"
                )

        def _test_single_device_reservations_only(self, device_type: DeviceType):
            """Check the UI content for when there are only reservations for a single device type"""
            self._test_single_device_reservations_or_rentals_only(
                device_type=device_type,
                data_type="reservations",
                time_cols=["reservation_time"],
            )

        def _test_single_device_rentals_only(self, device_type: DeviceType):
            """Check the UI content for when there are only rentals for a single device type"""
            self._test_single_device_reservations_or_rentals_only(
                device_type=device_type,
                data_type="rentals",
                time_cols=["pickup_time", "return_time"],
            )

        def _test_empty_inventory(self, expected_num_warnings: int):
            """Check the UI content for when there are no devices in the inventory"""
            at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

            self.assertEqual(
                expected_num_warnings,
                sum("No Scooters in Inventory" in warning.value for warning in at.warning),
                "A warning message should be displayed that there are no Scooters"
            )
            self.assertEqual(
                expected_num_warnings,
                sum("No Wheelchairs in Inventory" in warning.value for warning in at.warning),
                "A warning message should be displayed that there are no Wheelchairs"
            )
            self.assertEqual(0, len(at.dataframe), "No dataframes should be displayed as there is no data")

        def _test_single_device_inventory_only(self, device_type: DeviceType):
            """Check the UI content for when there are only devices of one type in the inventory"""
            data = self._load_mock_data_from_json(device_type=device_type, data_type="inventory")
            mock_requests = MockRequests(mock_inventory_data=data)
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

            # a warning should NOT be displayed for the device that has inventory
            self.assertFalse(
                any(f"No {device_type.title()}s in Inventory" in warning.value for warning in at.warning),
                f'"No {device_type.title()}s in Inventory" should not appear as there are {device_type.value.lower()}s'
            )

            # a warning should be displayed for the device that does NOT have inventory
            other_device_type = DeviceType.SCOOTER if device_type == DeviceType.WHEELCHAIR else DeviceType.WHEELCHAIR
            self.assertTrue(
                any(f"No {other_device_type.title()}s in Inventory" in warning.value for warning in at.warning),
                f"A warning should be displayed for the {other_device_type.value.lower()} inventory"
            )

            # one dataframe should be displayed for the inventory
            self.assertEqual(1, len(at.dataframe), f"Missing dataframe for {device_type.value.lower()} inventory")
