import os
from typing import List

import pandas as pd
import requests

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

    def get_full_inventory(self) -> pd.DataFrame:
        """Get the full inventory of devices using the API."""
        response = requests.get(
            url=f"http://{self.api_host}:{self.api_port}/devices/get_full_inventory",
            timeout=DEFAULT_TIMEOUT)
        return pd.DataFrame([Device(**device).dict() for device in response.json()])

    def set_full_inventory(self, inventory: List[Device]):
        """Set the full inventory of devices using the API."""
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/set_full_inventory",
            json=[device.dict() for device in inventory],
            timeout=DEFAULT_TIMEOUT,
        )
        return response.status_code, response.json()
