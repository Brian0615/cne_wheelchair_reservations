import datetime
import os
from typing import List, Optional, Tuple

import pandas as pd
import requests

from common.constants import DeviceType, Location
from common.data_models import Device, NewRental, NewReservation, Reservation

DEFAULT_TIMEOUT = 5


class DataService:
    """Service class to interact with the API."""

    def __init__(
            self,
            api_host: str = os.environ["API_HOST"],
            api_port: str = os.environ["API_PORT"],
    ):
        self.api_host = api_host
        self.api_port = api_port

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

    def add_new_rental(self, new_rental: NewRental):
        """Add a new rental using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/reservations/add_new_rental",
            json=new_rental.model_dump(mode="json"),
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
