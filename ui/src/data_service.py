import os
from typing import List

import pandas as pd
import requests

from common.data_models.device import Device


class DataService:
    def __init__(
            self,
            api_host: str = os.environ["API_HOST"],
            api_port: str = os.environ["API_PORT"],
    ):
        self.api_host = api_host
        self.api_port = api_port

    def get_full_inventory(self) -> pd.DataFrame:
        response = requests.get(f"http://{self.api_host}:{self.api_port}/devices/get_full_inventory")
        return pd.DataFrame([Device(**device).dict() for device in response.json()])

    def set_full_inventory(self, inventory: List[Device]):
        response = requests.post(
            f"http://{self.api_host}:{self.api_port}/devices/set_full_inventory",
            json=[device.dict() for device in inventory],
        )
        return response.status_code, response.json()
