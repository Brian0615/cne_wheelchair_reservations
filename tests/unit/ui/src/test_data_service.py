import datetime
from unittest import TestCase
from unittest.mock import Mock, patch

import requests
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
