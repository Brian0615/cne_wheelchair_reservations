from typing import Dict, List, Optional
from unittest.mock import Mock

from common.constants import DeviceType, Location
from common.cne_dates import CNEDates

_CNE_YEAR = CNEDates.get_cne_year()
_DEFAULT_DATE = str(CNEDates.get_default_date())
_RESERVATION_FORM_DEFAULT_DATE = str(CNEDates.get_default_new_reservation_date())


class MockAPIResponses:
    def __init__(
            self,
            reservations: Optional[List[Dict]] = None,
            rentals: Optional[List[Dict]] = None,
            inventory: Optional[List[Dict]] = None,
            reservation_limit: int = 100,
            reservation_count: int = 0,
    ):
        self.reservations = reservations if reservations is not None else []
        self.rentals = rentals if rentals is not None else []
        self.inventory = inventory if inventory is not None else []
        self.reservation_limit = reservation_limit
        self.reservation_count = reservation_count

    def get(self, url, *args, **kwargs):
        if "download_rental_form" in url:
            return Mock(status_code=200, content=b"mock_pdf_content")
        if "get_full_inventory" in url:
            return Mock(status_code=200, json=Mock(return_value=self.inventory))
        if "get_available_devices" in url:
            available = [d["id"] for d in self.inventory if d.get("status") == "Available"]
            return Mock(status_code=200, json=Mock(return_value=available))
        if "get_reservations_on_date" in url:
            return Mock(status_code=200, json=Mock(return_value=self.reservations))
        if "get_rentals_on_date" in url:
            return Mock(status_code=200, json=Mock(return_value=self.rentals))
        if "get_reservation_count" in url:
            return Mock(
                status_code=200,
                json=Mock(return_value=[
                    # Use the new-reservation default date (tomorrow) so capacity checks work
                    {"cne_year": _CNE_YEAR, "date": _RESERVATION_FORM_DEFAULT_DATE,
                     "device_type": DeviceType.SCOOTER.value,
                     "location": Location.BLC.value, "count": self.reservation_count},
                ]),
            )
        if "settings/get" in url:
            return Mock(status_code=200, json=Mock(return_value=self.reservation_limit))
        raise ValueError(f"Unexpected GET URL: {url}")

    @staticmethod
    def post(url, *args, **kwargs):
        if "change_device" in url:
            return Mock(status_code=200, json=Mock(return_value={}))
        if "complete_rental" in url:
            return Mock(status_code=200, json=Mock(return_value={}))
        if "update_reservation_status" in url:
            return Mock(status_code=200, json=Mock(return_value={}))
        raise ValueError(f"Unexpected POST URL: {url}")

    @staticmethod
    def put(url, *args, **kwargs):
        if "add_new_rental" in url:
            return Mock(status_code=200, json=Mock(return_value={"id": "S0820001"}))
        if "add_new_reservation" in url:
            return Mock(status_code=200, json=Mock(return_value={"id": "S0820001"}))
        if "update_reservation" in url:
            return Mock(status_code=200, json=Mock(return_value={}))
        if "update_settings" in url:
            return Mock(status_code=200, json=Mock(return_value={}))
        raise ValueError(f"Unexpected PUT URL: {url}")
