import datetime
import os
from functools import wraps
from typing import List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st

from common.constants import DeviceType, Location, DeviceStatus
from common.data_models import (
    ChangeDeviceInfo,
    CompletedRental,
    Device,
    NewRental,
    NewReservation,
    RentalSummary,
    Reservation,
)
from common.utils import get_default_timezone

DEFAULT_TIMEOUT = 5


def auto_process_api_errors(func):
    """Automatically process API errors and raise appropriate exceptions."""

    @wraps(func)
    def wrapper(data_service, *args, **kwargs):
        """Wrap the function and process API errors."""
        try:
            return func(data_service, *args, **kwargs)
        except requests.ConnectionError as exc:
            st.error(
                f"""
                **API Connection Error**: Unable to connect to the API. Please verify the API is running and accessible.
                 * Host: {data_service.api_host}
                 * Port: {data_service.api_port}
                """
            )
            with st.expander(label="Full Error Traceback"):
                st.write(exc)
            raise
        except Exception as exc:
            st.error(f"**API Error**: {exc}")
            raise

    return wrapper


# pylint: disable=no-self-argument
class DataService:
    """Service class to interact with the API."""

    def __init__(self, api_host: Optional[str] = None, api_port: Optional[str] = None):
        self.api_host = api_host if api_host is not None else os.environ["API_HOST"]
        self.api_port = api_port if api_port is not None else os.environ["API_PORT"]

    # ==============================
    # RESERVATIONS
    # ==============================

    @auto_process_api_errors
    def add_new_reservation(self, reservation: NewReservation):
        """Add a new reservation using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/reservations/add_new_reservation",
            json=reservation.model_dump(mode="json"),
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    @auto_process_api_errors
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

    @st.cache_data(ttl=60)
    @auto_process_api_errors
    def get_reservations_on_date(
            _self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
            exclude_picked_up_reservations: bool = False,
    ) -> pd.DataFrame:
        """Get the reservations on a specific date using the API."""

        response = requests.get(
            f"http://{_self.api_host}:{_self.api_port}/reservations/get_reservations_on_date",
            params={
                "date": date.strftime("%Y-%m-%d"),
                "device_type": device_type,
                "exclude_picked_up_reservations": exclude_picked_up_reservations,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        reservations = response.json()
        reservations = pd.DataFrame([Reservation(**reservation).model_dump() for reservation in reservations])
        if reservations.empty:
            return reservations
        reservations["reservation_time"] = (
            pd.to_datetime(reservations["reservation_time"], utc=True).dt.tz_convert(get_default_timezone())
        )
        return reservations

    # ==============================
    # RENTALS
    # ==============================

    @auto_process_api_errors
    def get_rentals_on_date(
            self,
            rental_date: datetime.date,
            device_type: Optional[DeviceType] = None,
            in_progress_rentals_only: bool = False,
    ) -> pd.DataFrame:
        """Get the rentals on a specific date using the API."""
        response = requests.get(
            f"http://{self.api_host}:{self.api_port}/rentals/get_rentals_on_date",
            params={
                "date": rental_date.strftime("%Y-%m-%d"),
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

    @auto_process_api_errors
    def add_new_rental(self, new_rental: NewRental):
        """Add a new rental using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/rentals/add_new_rental",
            json=new_rental.model_dump(mode="json"),
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    @auto_process_api_errors
    def change_rental_device(self, change_device_info: ChangeDeviceInfo):
        """Change the device of a rental using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/rentals/change_device",
            json=change_device_info.model_dump(mode="json"),
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    @auto_process_api_errors
    def complete_rental(self, completed_rental: CompletedRental):
        """Complete a rental using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/rentals/complete_rental",
            json=completed_rental.model_dump(mode="json"),
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    # ==============================
    # DEVICES
    # ==============================

    @auto_process_api_errors
    def get_available_devices(self, device_type: DeviceType, location: Location):
        """Get the available devices of a specific type at a specific location using the API."""
        response = requests.get(
            url=f"http://{self.api_host}:{self.api_port}/devices/get_available_devices",
            params={"device_type": device_type, "location": location},
            timeout=DEFAULT_TIMEOUT,
        )
        return response.json()

    @auto_process_api_errors
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

    @auto_process_api_errors
    def add_devices(self, devices: List[Device]):
        """Add devices to the inventory using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/add",
            json=[device.model_dump(mode="json") for device in devices],
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    @auto_process_api_errors
    def update_devices_location(self, device_ids: List[str], location: Location):
        """Update the location of devices using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/update_location",
            params={"location": location},
            json=device_ids,
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    @auto_process_api_errors
    def update_devices_status(self, device_ids: List[str], status: DeviceStatus):
        """Update the status of devices using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/update_status",
            params={"status": status},
            json=device_ids,
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    @auto_process_api_errors
    def remove_devices(self, device_ids: List[str]):
        """Remove devices from the inventory using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/remove",
            json=device_ids,
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    # ==============================
    # RENTAL FORMS
    # ==============================

    @auto_process_api_errors
    def upload_rental_form(self, pdf_bytes: bytes, rental_id: str):
        """Upload a rental form to S3 using the API."""
        response = requests.put(
            f"http://{self.api_host}:{self.api_port}/forms/upload_rental_form",
            params={"rental_id": rental_id},
            files={"pdf_bytes": pdf_bytes},
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()
