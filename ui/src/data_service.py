import datetime
import os
from functools import wraps
from typing import Any, Callable, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st
from pydantic import BaseModel

from common.constants import DeviceStatus, DeviceType, Location, ReservationStatus
from common.data_models import (
    ChangeDeviceInfo,
    CompletedRental,
    Device,
    NewDevice,
    NewRental,
    NewReservation,
    RentalSummary,
    Reservation,
)
from common.logger import initialize_logger, timeit
from ui.src.constants import CNEDates

logger = initialize_logger()


class APIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, message: str, request_data: Optional[dict] = None, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        st.error(f"**API Error**: {message}")
        if request_data or details:
            with st.expander(label="Full Error Traceback"):
                if request_data:
                    st.text("Request Data")
                    st.write(request_data)
                if details:
                    st.text("Error Message")
                    st.write(details)

DEFAULT_CACHE_TTL = 60
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
        except APIError:
            return None
        except Exception as exc:
            st.error(f"**API Error**: {exc}")
            raise

    return wrapper


# pylint: disable=no-self-argument
# noinspection PyMethodParameters
class DataService:
    """Service class to interact with the API."""

    def __init__(self, api_host: Optional[str] = None, api_port: Optional[str] = None):
        self.api_host = api_host if api_host is not None else os.environ["API_HOST"]
        self.api_port = api_port if api_port is not None else os.environ["API_PORT"]

    # ==============================
    # HELPER FUNCTIONS
    # ==============================

    # pylint: disable=too-many-arguments
    def _make_request(
            self,
            request_method: Callable,
            url_path: str,
            params: Optional[dict] = None,
            json: Optional[Any] = None,
            timeout: Optional[int] = DEFAULT_TIMEOUT,
    ):
        if isinstance(json, BaseModel):
            json = json.model_dump(mode="json")
        response = request_method(
            url=f"http://{self.api_host}:{self.api_port}/{url_path}",
            params=params,
            json=json,
            timeout=timeout,
        )
        if response.status_code == 200:
            return response
        if response.status_code == 404:
            raise APIError(message=f"Resource not found at `{url_path}`. Please check the URL and try again.",)
        if response.status_code == 422:
            raise APIError(
                message=f"Invalid request to `{url_path}`. Please check the parameters and try again.",
                request_data={"params": params, "json": json},
                details=response.json()
            )
        raise APIError(message=response.json())


    # ==============================
    # DEVICES
    # ==============================

    def _clear_devices_functions_cache(self):
        self.get_available_device_ids.clear()
        self.get_full_inventory.clear()

    @timeit(logger=logger)
    @auto_process_api_errors
    def add_devices(self, devices: List[NewDevice]):
        """Add devices to the inventory using the API."""
        response = self._make_request(
            request_method=requests.post,
            url_path="devices/add",
            json=[device.model_dump(mode="json") for device in devices]
        )
        self._clear_devices_functions_cache()
        return response.status_code, response.json()


    @st.cache_data(ttl=DEFAULT_CACHE_TTL, show_spinner=False)
    @timeit(logger=logger)
    @auto_process_api_errors
    def get_available_device_ids(_self, device_type: DeviceType, location: Optional[Location] = None):
        """Get the available devices of a specific type at a specific location using the API (location optional)."""
        params = {"cne_year": CNEDates.get_cne_year(), "device_type": device_type}
        if location is not None:
            params["location"] = location
        response = _self._make_request(
            request_method=requests.get,
            url_path="devices/get_available_devices",
            params=params,
        )
        return response.json()

    # pylint: disable=not-an-iterable
    @st.cache_data(ttl=DEFAULT_CACHE_TTL, show_spinner=False)
    @timeit(logger=logger)
    @auto_process_api_errors
    def get_full_inventory(_self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get the full inventory of devices using the API."""
        response = _self._make_request(
            request_method=requests.get,
            url_path="devices/get_full_inventory",
            params={"cne_year": CNEDates.get_cne_year()},
        )
        inventory = pd.DataFrame([Device(**device).model_dump(mode="json") for device in response.json()])
        if inventory.empty:
            inventory = pd.DataFrame(data={field: [] for field in Device.model_fields}, dtype=str)
        inventory = inventory.sort_values(by="id", ascending=True).reset_index(drop=True)

        return (
            inventory[inventory["type"] == DeviceType.SCOOTER],
            inventory[inventory["type"] == DeviceType.WHEELCHAIR],
        )

    @timeit(logger=logger)
    @auto_process_api_errors
    def remove_devices(self, device_ids: List[str]):
        """Remove devices from the inventory using the API."""
        response = self._make_request(
            request_method=requests.post,
            url_path="devices/remove",
            params={"cne_year": CNEDates.get_cne_year()},
            json=device_ids,
        )
        self._clear_devices_functions_cache()
        return response.status_code, response.json()

    @timeit(logger=logger)
    @auto_process_api_errors
    def update_devices_location(self, device_ids: List[str], location: Location):
        """Update the location of devices using the API."""
        response = self._make_request(
            request_method=requests.post,
            url_path="devices/update_location",
            params={"cne_year": CNEDates.get_cne_year(), "location": location},
            json=device_ids,
        )
        self._clear_devices_functions_cache()
        return response.status_code, response.json()

    @timeit(logger=logger)
    @auto_process_api_errors
    def update_devices_status(self, device_ids: List[str], status: DeviceStatus):
        """Update the status of devices using the API."""
        response = self._make_request(
            request_method=requests.post,
            url_path="devices/update_status",
            params={"cne_year": CNEDates.get_cne_year(), "status": status},
            json=device_ids,
        )
        self._clear_devices_functions_cache()
        return response.status_code, response.json()

    # ==============================
    # RENTALS
    # ==============================

    def _clear_rentals_functions_cache(self):
        self.get_rentals_on_date.clear()

    @auto_process_api_errors
    def add_new_rental(self, new_rental: NewRental):
        """Add a new rental using the API."""
        response = self._make_request(request_method=requests.post, url_path="rentals/add", json=new_rental)
        self._clear_rentals_functions_cache()
        return response.status_code, response.json()

    @st.cache_data(ttl=DEFAULT_CACHE_TTL, show_spinner=False)
    @auto_process_api_errors
    def get_rentals_on_date(
            _self,
            rental_date: datetime.date,
            device_type: Optional[DeviceType] = None,
            in_progress_rentals_only: bool = False,
    ) -> pd.DataFrame:
        """Get the rentals on a specific date using the API."""
        response = _self._make_request(
            request_method=requests.get,
            url_path="rentals/get_rentals_on_date",
            params={
                "date": rental_date.strftime("%Y-%m-%d"),
                "device_type": device_type,
                "in_progress_rentals_only": in_progress_rentals_only,
            },
        )
        rentals = response.json()
        rentals = pd.DataFrame([RentalSummary(**rental).model_dump() for rental in rentals])
        if rentals.empty:
            return rentals
        return rentals.sort_values(by="id")

    @auto_process_api_errors
    def change_rental_device(self, change_device_info: ChangeDeviceInfo):
        """Change the device of a rental using the API."""
        response = self._make_request(
            request_method=requests.post,
            url_path="rentals/change_device",
            json=change_device_info.model_dump(mode="json"),
        )
        self._clear_devices_functions_cache()
        self._clear_rentals_functions_cache()
        return response.status_code, response.json()

    @auto_process_api_errors
    def complete_rental(self, completed_rental: CompletedRental):
        """Complete a rental using the API."""
        response = self._make_request(
            request_method=requests.post,
            url_path="rentals/complete_rental",
            json=completed_rental.model_dump(mode="json"),
        )
        self._clear_devices_functions_cache()
        self._clear_rentals_functions_cache()
        return response.status_code, response.json()

    # ==============================
    # RESERVATIONS
    # ==============================

    def _clear_reservations_functions_cache(self):
        self.get_reservations_on_date.clear()

    @timeit(logger=logger)
    @auto_process_api_errors
    def add_new_reservation(self, reservation: NewReservation):
        """Add a new reservation using the API."""
        response = self._make_request(request_method=requests.post, url_path="reservations/add", json=reservation)
        self.get_reservations_on_date.clear()
        return response.status_code, response.json()

    @st.cache_data(ttl=DEFAULT_CACHE_TTL, show_spinner=False)
    @timeit(logger=logger)
    @auto_process_api_errors
    def get_reservations_on_date(
            _self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
            exclude_picked_up_reservations: bool = False,
    ) -> pd.DataFrame:
        """Get the reservations on a specific date using the API."""

        response = _self._make_request(
            request_method=requests.get,
            url_path="reservations/get_reservations_on_date",
            params={
                "date": date.strftime("%Y-%m-%d"),
                "device_type": device_type,
                "exclude_picked_up_reservations": exclude_picked_up_reservations,
            },
        )
        reservations = response.json()
        reservations = pd.DataFrame([Reservation(**reservation).model_dump() for reservation in reservations])
        if reservations.empty:
            return reservations
        reservations["reservation_time"] = pd.to_datetime(reservations["reservation_time"], utc=True)
        return reservations

    @timeit(logger=logger)
    @auto_process_api_errors
    def update_reservation(self, reservation: Reservation):
        """Update an existing reservation using the API."""
        response = self._make_request(
            request_method=requests.post,
            url_path="reservations/update_reservation",
            json=reservation,
        )
        self._clear_reservations_functions_cache()
        return response.status_code

    @timeit(logger=logger)
    @auto_process_api_errors
    def update_reservation_status(self, reservation_id: str, status: ReservationStatus):
        """Update the status of a reservation using the API."""
        response = self._make_request(
            request_method=requests.post,
            url_path="reservations/update_reservation_status",
            params={
                "cne_year": CNEDates.get_cne_year(),
                "reservation_id": reservation_id,
                "reservation_status": status,
            },
        )
        self._clear_reservations_functions_cache()
        return response.status_code

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
