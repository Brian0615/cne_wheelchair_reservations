from typing import Dict, List, Optional
from unittest.mock import Mock

from common.constants import DeviceStatus
from common.data_models import ChatRequest, Device


# pylint: disable=too-few-public-methods
class MockRequests:
    """Mock requests for the Home page"""

    def __init__(
            self,
            mock_inventory_data: Optional[List[Dict]] = None,
            mock_reservations_data: Optional[List[Dict]] = None,
            mock_rentals_data: Optional[List[Dict]] = None,
            mock_chat_response: str = "This is a mocked chatbot response.",
            mock_chat_model: str = "gemini-3.5-flash-lite",
            mock_chat_input_tokens: int = 80,
            mock_chat_output_tokens: int = 20,
            mock_chat_cache_read_tokens: int = 0,
    ):
        self.mock_inventory_data = mock_inventory_data if mock_inventory_data is not None else []
        self.mock_reservations_data = mock_reservations_data if mock_reservations_data is not None else []
        self.mock_rentals_data = mock_rentals_data if mock_rentals_data is not None else []
        self.mock_chat_response = mock_chat_response
        self.mock_chat_model = mock_chat_model
        self.mock_chat_input_tokens = mock_chat_input_tokens
        self.mock_chat_output_tokens = mock_chat_output_tokens
        self.mock_chat_cache_read_tokens = mock_chat_cache_read_tokens

    def mock_requests_get(self, url, *args, **kwargs):  # pylint: disable=unused-argument,too-many-return-statements
        """Mock the requests.get method"""
        if "download_rental_form" in url:
            return Mock(status_code=200, content=b"Mocked rental form content")
        if "get_full_inventory" in url:
            return Mock(status_code=200, json=Mock(return_value=self.mock_inventory_data))
        if "get_available_devices" in url:
            return Mock(
                status_code=200,
                json=Mock(
                    return_value=[
                        x["id"] for x in self.mock_inventory_data
                        if Device(**x).status == DeviceStatus.AVAILABLE
                    ]
                )
            )
        if "get_reservations_on_date" in url:
            return Mock(status_code=200, json=Mock(return_value=self.mock_reservations_data))
        if "get_rentals_on_date" in url:
            return Mock(status_code=200, json=Mock(return_value=self.mock_rentals_data))
        if "get_reservation_count" in url:
            return Mock(
                status_code=200,
                json=Mock(return_value=[
                    {"cne_year": 2025, "date": "2025-08-15", "device_type": "Scooter", "location": "BLC", "count": 5}
                ]),
            )
        if "settings/get" in url:
            return Mock(status_code=200, json=Mock(return_value=100))
        raise ValueError(f"Unsupported API url for mocking requests.get: {url}")

    def mock_requests_post(self, url, *args, **kwargs):  # pylint: disable=unused-argument
        """Mock the requests.post method"""
        if "change_device" in url:
            return Mock(status_code=200)
        if "complete_rental" in url:
            return Mock(status_code=200, json=Mock(return_value={}))
        if "update_reservation_status" in url:
            return Mock(status_code=200)
        if "chat/ask" in url:
            # validate against the real request model, mirroring the API, so a payload the real
            # endpoint would reject (e.g. extra keys) fails here too instead of only in production
            ChatRequest(**kwargs["json"])
            return Mock(
                status_code=200,
                json=Mock(return_value={
                    "answer": self.mock_chat_response,
                    "model": self.mock_chat_model,
                    "input_tokens": self.mock_chat_input_tokens,
                    "output_tokens": self.mock_chat_output_tokens,
                    "cache_read_tokens": self.mock_chat_cache_read_tokens,
                    "total_tokens": self.mock_chat_input_tokens + self.mock_chat_output_tokens,
                }),
            )
        raise ValueError(f"Unsupported API url for mocking requests.post: {url}")

    @staticmethod
    def mock_requests_put(url, *args, **kwargs):  # pylint: disable=unused-argument
        """Mock the requests.put method"""
        raise ValueError(f"Unsupported API url for mocking requests.put: {url}")
