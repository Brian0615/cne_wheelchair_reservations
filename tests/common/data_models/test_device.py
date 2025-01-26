import unittest

from common.constants import DeviceStatus, DeviceType, Location
from common.data_models.device import Device


class TestDevice(unittest.TestCase):
    """Test the Device class."""

    def test_check_id(self):
        """Test the check_id method."""
        with self.assertRaises(ValueError):
            Device(id="W01", type=DeviceType.SCOOTER, status=DeviceStatus.AVAILABLE, location=Location.BLC)
        with self.assertRaises(ValueError):
            Device(id="S01", type=DeviceType.WHEELCHAIR, status=DeviceStatus.AVAILABLE, location=Location.BLC)
