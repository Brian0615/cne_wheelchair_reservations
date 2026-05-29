"""Shared mock data constants used by both unit and workflow tests."""
from typing import Dict, List

from common.constants import DeviceType, Location, PaymentMethod, RentalStatus, ReservationStatus
from ui.src.constants import CNEDates

_CNE_YEAR = CNEDates.get_cne_year()
_DEFAULT_DATE = str(CNEDates.get_default_date())
_RESERVATION_FORM_DEFAULT_DATE = str(CNEDates.get_default_new_reservation_date())

MOCK_SCOOTER_RESERVATIONS: List[Dict] = [
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820001",
        "date": _DEFAULT_DATE,
        "device_type": DeviceType.SCOOTER.value,
        "name": "Alice Smith",
        "phone_number": "9052938402",
        "location": Location.BLC.value,
        "reservation_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
        "status": ReservationStatus.RESERVED.value,
        "rental_id": None,
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820002",
        "date": _DEFAULT_DATE,
        "device_type": DeviceType.SCOOTER.value,
        "name": "Bob Jones",
        "phone_number": "4168202370",
        "location": Location.PG.value,
        "reservation_time": f"{_DEFAULT_DATE}T14:00:00-04:00",
        "status": ReservationStatus.CONFIRMED.value,
        "rental_id": None,
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820003",
        "date": _DEFAULT_DATE,
        "device_type": DeviceType.SCOOTER.value,
        "name": "Carol White",
        "phone_number": "4372950218",
        "location": Location.BLC.value,
        "reservation_time": f"{_DEFAULT_DATE}T09:00:00-04:00",
        "status": ReservationStatus.CANCELLED.value,
        "rental_id": None,
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820004",
        "date": _DEFAULT_DATE,
        "device_type": DeviceType.SCOOTER.value,
        "name": "Dave Brown",
        "phone_number": "9052938402",
        "location": Location.PG.value,
        "reservation_time": f"{_DEFAULT_DATE}T11:00:00-04:00",
        "status": ReservationStatus.PICKED_UP.value,
        "rental_id": "S0820001",
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820005",
        "date": _DEFAULT_DATE,
        "device_type": DeviceType.SCOOTER.value,
        "name": "Eve Davis",
        "phone_number": "4168203702",
        "location": Location.BLC.value,
        "reservation_time": f"{_DEFAULT_DATE}T13:00:00-04:00",
        "status": ReservationStatus.COMPLETED.value,
        "rental_id": "S0820002",
        "notes": "",
    },
]

MOCK_WHEELCHAIR_RESERVATIONS: List[Dict] = [
    {
        "cne_year": _CNE_YEAR,
        "id": "W0820001",
        "date": _DEFAULT_DATE,
        "device_type": DeviceType.WHEELCHAIR.value,
        "name": "Frank Miller",
        "phone_number": "9052938402",
        "location": Location.BLC.value,
        "reservation_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
        "status": ReservationStatus.RESERVED.value,
        "rental_id": None,
        "notes": "",
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "W0820002",
        "date": _DEFAULT_DATE,
        "device_type": DeviceType.WHEELCHAIR.value,
        "name": "Grace Wilson",
        "phone_number": "4168202370",
        "location": Location.PG.value,
        "reservation_time": f"{_DEFAULT_DATE}T15:00:00-04:00",
        "status": ReservationStatus.CONFIRMED.value,
        "rental_id": None,
        "notes": "",
    },
]

# RentalSummary fields only (no address, city, fee_payment_method, etc.)
MOCK_SCOOTER_RENTALS: List[Dict] = [
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820001",
        "date": _DEFAULT_DATE,
        "name": "Alice Smith",
        "phone_number": "+1 416 820 3702",
        "device_type": DeviceType.SCOOTER.value,
        "device_id": "S01",
        "pickup_location": Location.BLC.value,
        "pickup_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
        "status": RentalStatus.IN_PROGRESS.value,
        "deposit_payment_method": PaymentMethod.CREDIT_CARD.value,
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
        "device_type": DeviceType.SCOOTER.value,
        "device_id": "S02",
        "pickup_location": Location.BLC.value,
        "pickup_time": f"{_DEFAULT_DATE}T11:00:00-04:00",
        "status": RentalStatus.COMPLETED.value,
        "deposit_payment_method": PaymentMethod.CASH.value,
        "return_location": Location.PG.value,
        "return_time": f"{_DEFAULT_DATE}T16:00:00-04:00",
        "items_left_behind": [],
        "notes": "",
        "reservation_id": None,
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "S0820003",
        "date": _DEFAULT_DATE,
        "name": "Charlie Green",
        "phone_number": "4165551234",
        "device_type": DeviceType.SCOOTER.value,
        "device_id": "S03",
        "pickup_location": Location.PG.value,
        "pickup_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
        "status": RentalStatus.IN_PROGRESS.value,
        "deposit_payment_method": PaymentMethod.CASH.value,
        "return_location": None,
        "return_time": None,
        "items_left_behind": [],
        "notes": "",
        "reservation_id": None,
    },
]

MOCK_SCOOTER_RENTALS_BLC: List[Dict] = [x for x in MOCK_SCOOTER_RENTALS if x["pickup_location"] == Location.BLC.value]

MOCK_SCOOTER_RENTALS_PG: List[Dict] = [x for x in MOCK_SCOOTER_RENTALS if x["pickup_location"] == Location.PG.value]

MOCK_WHEELCHAIR_RENTALS: List[Dict] = [
    {
        "cne_year": _CNE_YEAR,
        "id": "W0820001",
        "date": _DEFAULT_DATE,
        "name": "Frank Miller",
        "phone_number": "9052938402",
        "device_type": DeviceType.WHEELCHAIR.value,
        "device_id": "W01",
        "pickup_location": Location.BLC.value,
        "pickup_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
        "status": RentalStatus.IN_PROGRESS.value,
        "deposit_payment_method": PaymentMethod.CASH.value,
        "return_location": None,
        "return_time": None,
        "items_left_behind": [],
        "notes": "",
        "reservation_id": None,
    },
    {
        "cne_year": _CNE_YEAR,
        "id": "W0820002",
        "date": _DEFAULT_DATE,
        "name": "Diana Black",
        "phone_number": "4165559876",
        "device_type": DeviceType.WHEELCHAIR.value,
        "device_id": "W02",
        "pickup_location": Location.PG.value,
        "pickup_time": f"{_DEFAULT_DATE}T11:00:00-04:00",
        "status": RentalStatus.IN_PROGRESS.value,
        "deposit_payment_method": PaymentMethod.CREDIT_CARD.value,
        "return_location": None,
        "return_time": None,
        "items_left_behind": [],
        "notes": "",
        "reservation_id": None,
    },
]

MOCK_WHEELCHAIR_RENTALS_BLC: List[Dict] = [x for x in MOCK_WHEELCHAIR_RENTALS if
                                           x["pickup_location"] == Location.BLC.value]

MOCK_WHEELCHAIR_RENTALS_PG: List[Dict] = [x for x in MOCK_WHEELCHAIR_RENTALS if
                                          x["pickup_location"] == Location.PG.value]

MOCK_SCOOTER_INVENTORY: List[Dict] = [
    {"cne_year": _CNE_YEAR, "id": "S01", "type": DeviceType.SCOOTER.value, "status": "Available",
     "location": Location.BLC.value},
    {"cne_year": _CNE_YEAR, "id": "S02", "type": DeviceType.SCOOTER.value, "status": "Available",
     "location": Location.BLC.value},
    {"cne_year": _CNE_YEAR, "id": "S03", "type": DeviceType.SCOOTER.value, "status": "Backup",
     "location": Location.PG.value},
    {"cne_year": _CNE_YEAR, "id": "S04", "type": DeviceType.SCOOTER.value, "status": "Rented",
     "location": Location.BLC.value},
]

MOCK_WHEELCHAIR_INVENTORY: List[Dict] = [
    {"cne_year": _CNE_YEAR, "id": "W01", "type": DeviceType.WHEELCHAIR.value, "status": "Available",
     "location": Location.BLC.value},
    {"cne_year": _CNE_YEAR, "id": "W02", "type": DeviceType.WHEELCHAIR.value, "status": "Available",
     "location": Location.PG.value},
    {"cne_year": _CNE_YEAR, "id": "W03", "type": DeviceType.WHEELCHAIR.value, "status": "Rented",
     "location": Location.BLC.value},
]

MOCK_FULL_INVENTORY: List[Dict] = MOCK_SCOOTER_INVENTORY + MOCK_WHEELCHAIR_INVENTORY

MOCK_IN_PROGRESS_RENTAL_WITH_ITEMS: Dict = {
    "cne_year": _CNE_YEAR,
    "id": "S0820003",
    "date": _DEFAULT_DATE,
    "name": "Carol White",
    "phone_number": "4372950218",
    "device_type": DeviceType.SCOOTER.value,
    "device_id": "S03",
    "pickup_location": Location.BLC.value,
    "pickup_time": f"{_DEFAULT_DATE}T10:00:00-04:00",
    "status": RentalStatus.IN_PROGRESS.value,
    "deposit_payment_method": PaymentMethod.CASH.value,
    "return_location": None,
    "return_time": None,
    "items_left_behind": ["Walker", "Stroller"],
    "notes": "",
    "reservation_id": None,
}
