from typing import Dict, List, Optional
from unittest.mock import Mock

from ui.src.constants import CNEDates

_CNE_YEAR = CNEDates.get_cne_year()
_DEFAULT_DATE = str(CNEDates.get_default_date())
_RESERVATION_FORM_DEFAULT_DATE = str(CNEDates.get_default_new_reservation_date())

MOCK_SCOOTER_RESERVATIONS: List[Dict] = [
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820001",
        "date": _DEFAULT_DATE,
        "device_type": "Scooter",
        "name": "Alice Smith",
        "phone_number": "9052938402",
        "location": "BLC",
        "reservation_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
        "status": "Reserved",
        "rental_id": None,
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820002",
        "date": _DEFAULT_DATE,
        "device_type": "Scooter",
        "name": "Bob Jones",
        "phone_number": "4168202370",
        "location": "PG",
        "reservation_time": f"{_DEFAULT_DATE}T14:00:00-04:00",
        "status": "Confirmed",
        "rental_id": None,
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820003",
        "date": _DEFAULT_DATE,
        "device_type": "Scooter",
        "name": "Carol White",
        "phone_number": "4372950218",
        "location": "BLC",
        "reservation_time": f"{_DEFAULT_DATE}T09:00:00-04:00",
        "status": "Cancelled",
        "rental_id": None,
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820004",
        "date": _DEFAULT_DATE,
        "device_type": "Scooter",
        "name": "Dave Brown",
        "phone_number": "9052938402",
        "location": "PG",
        "reservation_time": f"{_DEFAULT_DATE}T11:00:00-04:00",
        "status": "Picked Up",
        "rental_id": "S0820001",
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820005",
        "date": _DEFAULT_DATE,
        "device_type": "Scooter",
        "name": "Eve Davis",
        "phone_number": "4168203702",
        "location": "BLC",
        "reservation_time": f"{_DEFAULT_DATE}T13:00:00-04:00",
        "status": "Completed",
        "rental_id": "S0820002",
        "notes": "",
    },
]

MOCK_WHEELCHAIR_RESERVATIONS: List[Dict] = [
    {
        "cne_year": _CNE_YEAR,
        "id": "W0820001",
        "date": _DEFAULT_DATE,
        "device_type": "Wheelchair",
        "name": "Frank Miller",
        "phone_number": "9052938402",
        "location": "BLC",
        "reservation_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
        "status": "Reserved",
        "rental_id": None,
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "W0820002",
        "date": _DEFAULT_DATE,
        "device_type": "Wheelchair",
        "name": "Grace Wilson",
        "phone_number": "4168202370",
        "location": "PG",
        "reservation_time": f"{_DEFAULT_DATE}T15:00:00-04:00",
        "status": "Confirmed",
        "rental_id": None,
        "notes": "",
    },
]

# RentalSummary fields only — extra fields like address, city, fee_payment_method, etc. are not
# part of this model and would cause a validation error.
MOCK_SCOOTER_RENTALS: List[Dict] = [
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820001",
        "date": _DEFAULT_DATE,
        "name": "Alice Smith",
        "phone_number": "+1 416 820 3702",
        "device_type": "Scooter",
        "device_id": "S01",
        "pickup_location": "BLC",
        "pickup_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
        "status": "In Progress",
        "deposit_payment_method": "Credit Card",
        "return_location": None,
        "return_time": None,
        "items_left_behind": [],
        "notes": "",
        "reservation_id": None,
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820002",
        "date": _DEFAULT_DATE,
        "name": "Bob Jones",
        "phone_number": "9052938402",
        "device_type": "Scooter",
        "device_id": "S02",
        "pickup_location": "BLC",
        "pickup_time": f"{_DEFAULT_DATE}T11:00:00-04:00",
        "status": "Completed",
        "deposit_payment_method": "Cash",
        "return_location": "PG",
        "return_time": f"{_DEFAULT_DATE}T16:00:00-04:00",
        "items_left_behind": [],
        "notes": "",
        "reservation_id": None,
    },
]

MOCK_WHEELCHAIR_RENTALS: List[Dict] = [
    {
        "cne_year": _CNE_YEAR,
        "id": "W0820001",
        "date": _DEFAULT_DATE,
        "name": "Frank Miller",
        "phone_number": "9052938402",
        "device_type": "Wheelchair",
        "device_id": "W01",
        "pickup_location": "BLC",
        "pickup_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
        "status": "In Progress",
        "deposit_payment_method": "Cash",
        "return_location": None,
        "return_time": None,
        "items_left_behind": [],
        "notes": "",
        "reservation_id": None,
    },
]

MOCK_SCOOTER_INVENTORY: List[Dict] = [
    {"cne_year": _CNE_YEAR, "id": "S01", "type": "Scooter", "status": "Available", "location": "BLC"},
    {"cne_year": _CNE_YEAR, "id": "S02", "type": "Scooter", "status": "Available", "location": "BLC"},
    {"cne_year": _CNE_YEAR, "id": "S03", "type": "Scooter", "status": "Backup", "location": "PG"},
    {"cne_year": _CNE_YEAR, "id": "S04", "type": "Scooter", "status": "Rented", "location": "BLC"},
]

MOCK_WHEELCHAIR_INVENTORY: List[Dict] = [
    {"cne_year": _CNE_YEAR, "id": "W01", "type": "Wheelchair", "status": "Available", "location": "BLC"},
    {"cne_year": _CNE_YEAR, "id": "W02", "type": "Wheelchair", "status": "Available", "location": "PG"},
    {"cne_year": _CNE_YEAR, "id": "W03", "type": "Wheelchair", "status": "Rented", "location": "BLC"},
]

MOCK_FULL_INVENTORY: List[Dict] = MOCK_SCOOTER_INVENTORY + MOCK_WHEELCHAIR_INVENTORY

# In-progress rental that has items left behind — used by complete_rental tests.
MOCK_IN_PROGRESS_RENTAL_WITH_ITEMS: Dict = {
    "cne_year": _CNE_YEAR,
    "id": "S0820003",
    "date": _DEFAULT_DATE,
    "name": "Carol White",
    "phone_number": "4372950218",
    "device_type": "Scooter",
    "device_id": "S03",
    "pickup_location": "BLC",
    "pickup_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
    "status": "In Progress",
    "deposit_payment_method": "Cash",
    "return_location": None,
    "return_time": None,
    "items_left_behind": ["Walker", "Stroller"],
    "notes": "",
    "reservation_id": None,
}


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
                    {"cne_year": _CNE_YEAR, "date": _RESERVATION_FORM_DEFAULT_DATE, "device_type": "Scooter",
                     "location": "BLC", "count": self.reservation_count},
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
