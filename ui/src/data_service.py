import datetime
import os
from typing import List, Optional, Tuple

import pandas as pd
import requests

from common.constants import DeviceType, Location
from common.data_models import (
    ChangeDeviceInfo,
    CompletedRental,
    Device,
    NewRental,
    NewReservation,
    RentalSummary,
    Reservation,
)
from ui.src.constants import CNEDates

DEFAULT_TIMEOUT = 5


class DataService:
    """Service class to interact with the API."""

    def __init__(
            self,
            api_host: Optional[str] = None,
            api_port: Optional[str] = None,
    ):
        self.api_host = api_host if api_host is not None else os.environ["API_HOST"]
        self.api_port = api_port if api_port is not None else os.environ["API_PORT"]

    def get_available_devices(self, device_type: DeviceType, location: Location):
        """Get the available devices of a specific type at a specific location using the API."""
        response = requests.get(
            url=f"http://{self.api_host}:{self.api_port}/devices/get_available_devices",
            params={"device_type": device_type, "location": location},
            timeout=DEFAULT_TIMEOUT,
        )
        return response.json()

    def get_full_inventory(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get the full inventory of devices using the API."""

        response = requests.get(
            url=f"http://{self.api_host}:{self.api_port}/devices/get_full_inventory",
            timeout=DEFAULT_TIMEOUT,
        )
        inventory = pd.DataFrame([Device(**device).model_dump(mode="json") for device in response.json()])
        if inventory.empty:
            inventory = pd.DataFrame(data={field: [] for field in Device.model_fields}, dtype=str)
        inventory = inventory.sort_values(by="id", ascending=True).reset_index(drop=True)

        return (
            inventory[inventory["type"] == DeviceType.SCOOTER],
            inventory[inventory["type"] == DeviceType.WHEELCHAIR],
        )

    def add_to_inventory(self, devices: List[Device]):
        """Add devices to the inventory using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/add_to_inventory",
            json=[device.model_dump(mode="json") for device in devices],
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    def update_inventory(self, inventory: List[Device]):
        """Set the full inventory of devices using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/update_inventory",
            json=[device.model_dump(mode="json") for device in inventory],
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    def add_new_reservation(self, reservation: NewReservation):
        """Add a new reservation using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/reservations/add_new_reservation",
            json=reservation.model_dump(mode="json"),
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    def get_rentals_on_date(
            self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
            in_progress_rentals_only: bool = False,
    ):
        """Get the rentals on a specific date using the API."""
        response = requests.get(
            f"http://{self.api_host}:{self.api_port}/rentals/get_rentals_on_date",
            params={
                "date": date.strftime("%Y-%m-%d"),
                "device_type": device_type,
                "in_progress_rentals_only": in_progress_rentals_only,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        rentals = response.json()
        rentals = pd.DataFrame([RentalSummary(**rental).model_dump() for rental in rentals])
        if rentals.empty:
            return rentals
        return rentals.sort_values(by="id")

    def get_all_rentals(self):
        """Get all rentals for the current year."""
        return {
            date: self.get_rentals_on_date(date)
            for date in CNEDates.get_cne_date_list(year=datetime.datetime.today().year)
        }

    def get_number_of_reservations_on_date(
            self,
            date: datetime.date,
            device_type: DeviceType,
            location: Location,
    ):
        """Get the number of reservations on a specific date using the API."""
        response = requests.get(
            f"http://{self.api_host}:{self.api_port}/reservations/get_number_of_reservations_on_date",
            params={
                "date": date.strftime("%Y-%m-%d"),
                "device_type": device_type,
                "location": location,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        return response.json()

    def get_reservations_on_date(
            self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
            exclude_picked_up_reservations: bool = False,
    ) -> pd.DataFrame:
        """Get the reservations on a specific date using the API."""

        response = requests.get(
            f"http://{self.api_host}:{self.api_port}/reservations/get_reservations_on_date",
            params={
                "date": date.strftime("%Y-%m-%d"),
                "device_type": device_type,
                "exclude_picked_up_reservations": exclude_picked_up_reservations,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        reservations = response.json()
        reservations = pd.DataFrame([Reservation(**reservation).model_dump() for reservation in reservations])
        return reservations

    def get_all_reservations(self):
        """Get all reservations for the current year."""
        return {
            date: self.get_reservations_on_date(date)
            for date in CNEDates.get_cne_date_list(year=datetime.datetime.today().year)
        }

    def add_new_rental(self, new_rental: NewRental):
        """Add a new rental using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/rentals/add_new_rental",
            json=new_rental.model_dump(mode="json"),
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    def change_rental_device(self, change_device_info: ChangeDeviceInfo):
        """Change the device of a rental using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/rentals/change_device",
            json=change_device_info.model_dump(mode="json"),
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    def complete_rental(self, completed_rental: CompletedRental):
        """Complete a rental using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/rentals/complete_rental",
            json=completed_rental.model_dump(mode="json"),
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    def update_devices_location(self, device_ids: List[str], location: Location):
        """Update the location of devices using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/update_location",
            params={"location": location},
            json=device_ids,
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()
