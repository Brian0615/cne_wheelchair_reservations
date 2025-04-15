import json
import os
from datetime import date, datetime
from typing import List, Optional
from unittest import TestCase
from unittest.mock import patch, MagicMock

import boto3
import numpy as np
import requests
import streamlit as st
from moto import mock_aws
from streamlit.testing.v1 import AppTest

from api.src.dynamodb_service import DynamoDBService
from common.constants import DeviceType, DeviceStatus, Location, PaymentMethod, RentalStatus, ReservationStatus
from common.data_models import CompletedRental, NewRental, NewReservation, Reservation
from common.utils import get_default_timezone
from tests.mock_requests import MockRequests
from ui.auth.local_authenticator import LocalAuthenticator
from ui.src.constants import CNEDates
from ui.src.signature import Signature


# pylint: disable=too-few-public-methods
class BaseTestCases:
    """Shared Test Cases"""

    @mock_aws
    class BaseDynamoDBServiceTest(TestCase):
        """Shared Test Cases for DynamoDB Service"""
        __DEFAULT_TABLE_KEY_SCHEMA = [
            {"AttributeName": "cne_year", "KeyType": "HASH"},
            {"AttributeName": "id", "KeyType": "RANGE"}
        ]
        __DEFAULT_ATTRIBUTE_DEFINITIONS = [
            {"AttributeName": "cne_year", "AttributeType": "N"},
            {"AttributeName": "id", "AttributeType": "S"}
        ]
        __DEFAULT_PROVISIONED_THROUGHPUT = {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}

        @classmethod
        def setUpClass(cls):
            cls.dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
            cls.devices_table = None
            cls.rentals_table = None
            cls.reservations_table = None
            cls.service = DynamoDBService()

        def setUp(self):
            if self.devices_table is not None:
                self.dynamodb.meta.client.delete_table(TableName="cne_devices")
            if self.rentals_table is not None:
                self.dynamodb.meta.client.delete_table(TableName="cne_rentals")
            if self.reservations_table is not None:
                self.dynamodb.meta.client.delete_table(TableName="cne_reservations")
            self.devices_table = self.dynamodb.create_table(
                TableName="cne_devices",
                KeySchema=self.__DEFAULT_TABLE_KEY_SCHEMA,
                AttributeDefinitions=self.__DEFAULT_ATTRIBUTE_DEFINITIONS,
                ProvisionedThroughput=self.__DEFAULT_PROVISIONED_THROUGHPUT,
            )
            self.rentals_table = self.dynamodb.create_table(
                TableName="cne_rentals",
                KeySchema=self.__DEFAULT_TABLE_KEY_SCHEMA,
                AttributeDefinitions=self.__DEFAULT_ATTRIBUTE_DEFINITIONS,
                ProvisionedThroughput=self.__DEFAULT_PROVISIONED_THROUGHPUT,
            )
            self.reservations_table = self.dynamodb.create_table(
                TableName="cne_reservations",
                KeySchema=self.__DEFAULT_TABLE_KEY_SCHEMA,
                AttributeDefinitions=self.__DEFAULT_ATTRIBUTE_DEFINITIONS,
                ProvisionedThroughput=self.__DEFAULT_PROVISIONED_THROUGHPUT,
            )

        @staticmethod
        def _generate_mock_new_reservation(overrides: Optional[dict] = None):
            reservation_params = {
                "cne_year": 2025,
                "date": date(2025, 8, 20),
                "device_type": DeviceType.SCOOTER,
                "location": Location.BLC,
                "reservation_time": get_default_timezone().localize(datetime(2025, 8, 20, 11, 30)),
                "name": "Test Name",
                "phone_number": "1234567890",
                "notes": "",
                "status": ReservationStatus.PENDING,
            }
            if overrides:
                for key, value in overrides.items():
                    reservation_params[key] = value
            return NewReservation(**reservation_params)

        def _generate_mock_reservation(self, overrides: Optional[dict] = None):
            reservation = self._generate_mock_new_reservation(overrides=overrides)
            return Reservation(**reservation.model_dump())

        @staticmethod
        def _generate_mock_completed_rental(overrides: Optional[dict] = None):
            """Generate mock data for a completed rental"""
            rental_params = {
                "cne_year": 2025,
                "id": "W0820001",
                "date": date(2025, 8, 20),
                "device_id": "W01",
                "reservation_id": "W0820001",
                "name": "Test Name",
                "return_location": Location.BLC,
                "return_time": get_default_timezone().localize(datetime(2025, 8, 20, 20, 28)),
                "return_staff_name": "Test Staff",
                "return_signature": Signature(signature_data=np.ones((100, 600, 4), dtype=np.uint8)).encode_as_base64(),
            }
            if overrides:
                for key, value in overrides.items():
                    rental_params[key] = value
            return CompletedRental(**rental_params)

        @staticmethod
        def _generate_mock_new_rental(overrides: Optional[dict] = None):
            rental_params = {
                "cne_year": 2025,
                "date": date(2025, 8, 20),
                "device_id": "W01",
                "device_type": DeviceType.WHEELCHAIR,
                "reservation_id": "W0820001",
                "pickup_location": Location.BLC,
                "pickup_time": get_default_timezone().localize(datetime(2025, 8, 20, 11, 28)),
                "status": RentalStatus.IN_PROGRESS,
                "name": "Test Name",
                "phone_number": "1234567890",
                "address": "1234 Test St",
                "city": "Test City",
                "province": "Test Province",
                "postal_code": "A1B2C3",
                "country": "Canada",
                "fee_payment_method": PaymentMethod.CREDIT_CARD,
                "fee_payment_amount": 50,
                "deposit_payment_method": PaymentMethod.CASH,
                "deposit_payment_amount": 100,
                "items_left_behind": [],
                "notes": None,
                "staff_name": "Test Staff",
                "signature": Signature(signature_data=np.ones((100, 600, 4), dtype=np.uint8)).encode_as_base64(),
            }
            if overrides:
                for key, value in overrides.items():
                    rental_params[key] = value
            return NewRental(**rental_params)


    class BaseFormFieldTest(TestCase):
        """Shared Test Cases for Form Fields"""

        def setUp(self):
            self.field_class = None
            self.expected_init_value = None
            raise NotImplementedError("Setup Function not Implemented")

        # pylint: disable=protected-access
        @staticmethod
        def _run_field(form_field_class, render: bool = False, disabled: bool = False, clear: bool = False, **kwargs):
            """Run the field, optionally rendering it"""
            field = form_field_class(key="test_key", label="Test Label", **kwargs)
            field.initialize_field()

            if render:
                field._render(disabled=disabled)

                if clear:
                    field.clear_field()

        @staticmethod
        def _get_field(at: AppTest):
            """Get the field from the AppTest"""
            raise NotImplementedError("Get Field not Implemented")

        def test_initialize_field(self):
            """Test initializing a new field"""
            self._test_initialize_field_without_kwargs()

        def _test_initialize_field_without_kwargs(self):
            """Helper function to test initializing a new field without any kwargs"""
            at = AppTest.from_function(script=self._run_field, args=(self.field_class,)).run()
            self.assertEqual(at.session_state["test_key"], self.expected_init_value)

        def _test_initialize_field_with_kwargs(self, kwargs_dict, expected_init_value):
            """Helper function to test initializing a new field with kwargs"""
            at = AppTest.from_function(script=self._run_field, args=(self.field_class,), kwargs=kwargs_dict).run()
            self.assertEqual(at.session_state["test_key"], expected_init_value)

        def test_render(self):
            """Test rendering a field"""
            self._test_render_without_kwargs()

        def _test_render_without_kwargs(self):
            for disabled in [True, False]:
                with self.subTest(f"Render with disabled={disabled}"):
                    at = AppTest.from_function(
                        script=self._run_field,
                        args=(self.field_class,),
                        kwargs={"render": True, "disabled": disabled},
                    ).run()
                    self._run_field_post_render_checks(at=at, disabled=disabled)

        def _test_render_with_kwargs(self, kwargs_dict):
            for disabled in [True, False]:
                with self.subTest(f"Render with disabled={disabled}"):
                    kwargs_dict["render"] = True
                    kwargs_dict["disabled"] = disabled
                    at = AppTest.from_function(
                        script=self._run_field,
                        args=(self.field_class,),
                        kwargs=kwargs_dict,
                    ).run()
                    self._run_post_render_checks(at=at, disabled=disabled)

        def _run_post_render_checks(self, at: AppTest, disabled: bool):
            """Run checks for a field after it is rendered"""
            self.assertEqual(self._get_field(at=at).disabled, disabled)
            self.assertEqual(self._get_field(at=at).label, "Test Label")
            self._run_field_post_render_checks(at=at, disabled=disabled)

            if not disabled:
                self._run_field_post_interaction_checks(at=at)

        def _run_field_post_render_checks(self, at: AppTest, disabled: bool):
            """Run field-specific checks for a field after it is rendered"""

            raise NotImplementedError("Run Post Render Checks not Implemented")

        def _run_field_post_interaction_checks(self, at: AppTest):
            """Run field-specific checks for a field after it is interacted with (assuming it is not disabled)"""

            raise NotImplementedError("Run Post Interaction Checks not Implemented")

        def test_clear_field(self):
            """Test clearing a field"""
            at = AppTest.from_function(
                script=self._run_field,
                args=(self.field_class,),
                kwargs={"render": True, "clear": True},
            ).run()
            with self.assertRaises(KeyError):
                _ = at.session_state["test_key"]

    class BaseUIPageTest(TestCase):
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
            with patch.object(LocalAuthenticator, "login", return_value=False):
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
                        with patch.object(LocalAuthenticator, "login", return_value=True):
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

        def _subtest_single_device_reservations_only(self, device_type: DeviceType):
            """Check the UI content for when there are only reservations for a single device type"""
            self._test_single_device_reservations_or_rentals_only(
                device_type=device_type,
                data_type="reservations",
                time_cols=["reservation_time"],
            )

        def _subtest_single_device_rentals_only(self, device_type: DeviceType):
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
                sum("No Scooters" in warning.value for warning in at.warning),
                "A warning message should be displayed that there are no Scooters"
            )
            self.assertEqual(
                expected_num_warnings,
                sum("No Wheelchairs" in warning.value for warning in at.warning),
                "A warning message should be displayed that there are no Wheelchairs"
            )
            self.assertEqual(0, len(at.dataframe), "No dataframes should be displayed as there is no data")

        def _subtest_single_device_inventory_only(self, device_type: DeviceType):
            """Check the UI content for when there are only devices of one type in the inventory"""
            data = self._load_mock_data_from_json(device_type=device_type, data_type="inventory")
            mock_requests = MockRequests(mock_inventory_data=data)
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

            # a warning should NOT be displayed for the device that has inventory
            self.assertFalse(
                any(f"No {device_type.title()}s" in warning.value for warning in at.warning),
                f'"No {device_type.title()}s" should not appear as there are {device_type.value.lower()}s'
            )

            # a warning should be displayed for the device that does NOT have inventory
            other_device_type = DeviceType.SCOOTER if device_type == DeviceType.WHEELCHAIR else DeviceType.WHEELCHAIR
            self.assertTrue(
                any(f"No {other_device_type.title()}s" in warning.value for warning in at.warning),
                f"A warning should be displayed for the {other_device_type.value.lower()} inventory"
            )

            # one dataframe should be displayed for the inventory
            self.assertEqual(1, len(at.dataframe), f"Missing dataframe for {device_type.value.lower()} inventory")

        def _subtest_filter_inventory(
                self,
                device_type: DeviceType,
                status: Optional[DeviceStatus] = None,
                location: Optional[Location] = None
        ):
            data = self._load_mock_data_from_json(device_type=device_type, data_type="inventory")
            mock_requests = MockRequests(mock_inventory_data=data)
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

            if status is not None:
                at.selectbox(key=f"{device_type.value.lower()}_status_filter").select(status)
                at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            if location is not None:
                at.selectbox(key=f"{device_type.value.lower()}_location_filter").select(location)
                at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

            expected_results = [
                device for device in data if (
                        (device["status"] == status or status is None)
                        and (device["location"] == location or location is None)
                )
            ]
            self.assertTrue(at.dataframe.len == 1, "No inventory displayed")
            self.assertEqual(
                len(expected_results),
                len(at.dataframe[0].value),
                "Incorrect number of devices displayed"
            )
