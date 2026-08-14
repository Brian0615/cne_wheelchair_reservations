import datetime
from unittest import TestCase
from unittest.mock import Mock, patch

import requests
import streamlit as st
from pydantic import BaseModel

from ui.src.data_service import DataService


class DummyBaseModel(BaseModel):
    """A dummy base model for testing purposes."""
    a: str
    b: datetime.date
    c: float


# pylint: disable=missing-class-docstring,missing-function-docstring
class TestDataService(TestCase):

    def setUp(self):
        self.data_service = DataService(api_host="test_host", api_port="1234")

    # pylint: disable=protected-access
    def test_make_request(self):
        with patch("requests.get", return_value=Mock(status_code=200, json=Mock(return_value={}))) as mock_get:
            self.data_service._make_request(
                request_method=requests.get,
                url_path="test_path",
                params={"cne_year": 1234},
                json={"key_a": "a", "key_b": "b"},
                timeout=100,
            )
            mock_get.assert_called_once_with(
                url="http://test_host:1234/test_path",
                params={"cne_year": 1234},
                json={"key_a": "a", "key_b": "b"},
                timeout=100,
            )
        with patch("requests.get", return_value=Mock(status_code=200, json=Mock(return_value={}))) as mock_get:
            self.data_service._make_request(
                request_method=requests.get,
                url_path="test_path",
                params={"cne_year": 1234},
                json=DummyBaseModel(a="a", b=datetime.date(2023, 10, 1), c=1.0),
                timeout=100,
            )
            mock_get.assert_called_once_with(
                url="http://test_host:1234/test_path",
                params={"cne_year": 1234},
                json={"a": "a", "b": "2023-10-01", "c": 1.0},
                timeout=100,
            )


# pylint: disable=missing-class-docstring,missing-function-docstring
class TestDataServiceCacheBypass(TestCase):
    """Tests proving the *_bypass_cache methods always hit the API without disturbing the
    shared st.cache_data cache that get_full_inventory/get_reservations_on_date/
    get_rentals_on_date use, unlike the previous approach of calling .clear() on them."""

    def setUp(self):
        self.data_service = DataService(api_host="test_host", api_port="1234")
        st.cache_data.clear()

    def test_get_full_inventory_bypass_cache_does_not_use_or_evict_the_shared_cache(self):
        with patch("requests.get", return_value=Mock(status_code=200, json=Mock(return_value=[]))) as mock_get:
            self.data_service.get_full_inventory()
            self.data_service.get_full_inventory()
            self.assertEqual(1, mock_get.call_count, "The second cached call should not hit the API")

            self.data_service.get_full_inventory_bypass_cache()
            self.assertEqual(2, mock_get.call_count, "The bypass call should always hit the API")

            self.data_service.get_full_inventory()
            self.assertEqual(2, mock_get.call_count, "The bypass call should not have evicted the shared cache")

    def test_get_reservations_on_date_bypass_cache_does_not_use_or_evict_the_shared_cache(self):
        date = datetime.date(2025, 8, 15)
        with patch("requests.get", return_value=Mock(status_code=200, json=Mock(return_value=[]))) as mock_get:
            self.data_service.get_reservations_on_date(date)
            self.data_service.get_reservations_on_date(date)
            self.assertEqual(1, mock_get.call_count, "The second cached call should not hit the API")

            self.data_service.get_reservations_on_date_bypass_cache(date)
            self.assertEqual(2, mock_get.call_count, "The bypass call should always hit the API")

            self.data_service.get_reservations_on_date(date)
            self.assertEqual(2, mock_get.call_count, "The bypass call should not have evicted the shared cache")

    def test_get_rentals_on_date_bypass_cache_does_not_use_or_evict_the_shared_cache(self):
        date = datetime.date(2025, 8, 15)
        with patch("requests.get", return_value=Mock(status_code=200, json=Mock(return_value=[]))) as mock_get:
            self.data_service.get_rentals_on_date(date)
            self.data_service.get_rentals_on_date(date)
            self.assertEqual(1, mock_get.call_count, "The second cached call should not hit the API")

            self.data_service.get_rentals_on_date_bypass_cache(date)
            self.assertEqual(2, mock_get.call_count, "The bypass call should always hit the API")

            self.data_service.get_rentals_on_date(date)
            self.assertEqual(2, mock_get.call_count, "The bypass call should not have evicted the shared cache")
