# pylint: disable=missing-function-docstring,protected-access

from common.constants import DeviceStatus, Location, DeviceType
from tests.unit.base_tests import BaseTestCases


class TestDynamoDBServiceHelpers(BaseTestCases.BaseDynamoDBServiceTest):
    """Test helper functions in DynamoDB Service"""

    def test_form_update_device_transact_dict(self):

        for expected_status, expected_type in [
                (None, None),
                (DeviceStatus.AVAILABLE, None),
                (None, DeviceType.WHEELCHAIR),
                (DeviceStatus.AVAILABLE, DeviceType.WHEELCHAIR)
        ]:
            with self.subTest(
                    expected_status=expected_status.name if expected_status else None,
                    expected_type=expected_type.name if expected_type else None):
                result = self.service._form_update_device_transact_dict(
                    cne_year=2023,
                    device_id="W01",
                    update_location=Location.BLC,
                    update_status=DeviceStatus.BACKUP,
                    expected_status=expected_status,
                    expected_type=expected_type
                )["Update"]
                self.assertEqual(result["Key"], {"cne_year": 2023, "id": "W01"})
                self.assertEqual(
                    "#status = :expected_status" in result["ConditionExpression"],
                    expected_status is not None
                )
                self.assertEqual(
                    "#type = :expected_type" in result["ConditionExpression"],
                    expected_type is not None
                )
                self.assertEqual(result["ExpressionAttributeValues"].get(":expected_status"), expected_status)
                self.assertEqual(result["ExpressionAttributeValues"].get(":expected_type"), expected_type)
