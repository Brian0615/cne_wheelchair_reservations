import os
from typing import List

import pandas as pd
import requests
import streamlit as st

from common.constants import DeviceType, Location
from common.data_models.device import Device

DEFAULT_TIMEOUT = 10


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
            timeout=DEFAULT_TIMEOUT)
        return response.json()

    def get_full_inventory(self, reset_cache=False) -> pd.DataFrame:
        """Get the full inventory of devices using the API."""

        @st.cache_data(ttl=60, show_spinner=False)
        def get_full_inventory_helper(host, port):
            response = requests.get(
                url=f"http://{host}:{port}/devices/get_full_inventory",
                timeout=DEFAULT_TIMEOUT)
            return pd.DataFrame([Device(**device).dict() for device in response.json()])

        if reset_cache:
            get_full_inventory_helper.clear()

        return get_full_inventory_helper(self.api_host, self.api_port)

    def add_to_inventory(self, devices: List[Device]):
        """Add devices to the inventory using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/add_to_inventory",
            json=[device.dict() for device in devices],
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()

    def update_inventory(self, inventory: List[Device]):
        """Set the full inventory of devices using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/update_inventory",
            json=[device.dict() for device in inventory],
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()
