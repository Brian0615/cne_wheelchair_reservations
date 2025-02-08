from typing import Dict, List, Optional

from unittest.mock import Mock


# pylint: disable=too-few-public-methods
class MockRequests:
    """Mock requests for the Home page"""

    def __init__(
            self,
            mock_inventory_data: Optional[List[Dict]] = None,
            mock_reservations_data: Optional[List[Dict]] = None,
            mock_rentals_data: Optional[List[Dict]] = None,
    ):
        self.mock_inventory = mock_inventory_data if mock_inventory_data is not None else []
        self.mock_reservations_data = mock_reservations_data if mock_reservations_data is not None else []
        self.mock_rentals_data = mock_rentals_data if mock_rentals_data is not None else []

    def mock_requests_get(self, url, *args, **kwargs):  # pylint: disable=unused-argument
        """Mock the requests.get method"""
        if "get_full_inventory" in url:
            return Mock(json=Mock(return_value=self.mock_inventory))
        if "get_reservations_on_date" in url:
            return Mock(json=Mock(return_value=self.mock_reservations_data))
        if "get_rentals_on_date" in url:
            return Mock(json=Mock(return_value=self.mock_rentals_data))
        raise ValueError(f"Unsupported API url for mocking requests.get: {url}")

    @staticmethod
    def mock_requests_post(url, *args, **kwargs):  # pylint: disable=unused-argument
        """Mock the requests.post method"""
        if "complete_rental" in url:
            return Mock(status_code=200, json=Mock(return_value={}))
        raise ValueError(f"Unsupported API url for mocking requests.post: {url}")

    @staticmethod
    def mock_requests_put(url, *args, **kwargs):  # pylint: disable=unused-argument
        """Mock the requests.put method"""
        raise ValueError(f"Unsupported API url for mocking requests.put: {url}")
