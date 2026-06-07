import datetime
from unittest import TestCase
from unittest.mock import MagicMock

import pandas as pd
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, ToolCallPart, ToolReturnPart

from api.src.chat_service import ChatService, _to_model_messages
from common.constants import DeviceStatus, DeviceType, Location
from common.data_models import ChatMessage, ChatRole, Device, RentalSummary
from common.utils import get_default_timezone


def _make_chat_service() -> ChatService:
    """Create a ChatService with a mocked DynamoDBService (no real AWS / agent involved)."""
    service = ChatService()
    service.db_service = MagicMock()
    service.cne_year = 2025
    return service


class TestChatServiceTools(TestCase):
    """Tests for the chatbot tool wrappers around DynamoDBService."""

    def setUp(self):
        self.service = _make_chat_service()

    # ── context tools ─────────────────────────────────────────────────────

    def test_get_today_returns_iso_date(self):
        today = datetime.datetime.now(get_default_timezone()).date().isoformat()
        self.assertEqual(today, self.service.get_today())

    # ── lookup tools ──────────────────────────────────────────────────────

    def test_lookup_rentals_on_date_converts_items(self):
        summary = RentalSummary(
            cne_year=2025,
            id="W0820001",
            date=datetime.date(2025, 8, 20),
            device_id="W01",
            device_type=DeviceType.WHEELCHAIR,
            reservation_id="W0820001",
            pickup_location=Location.BLC,
            pickup_time=get_default_timezone().localize(datetime.datetime(2025, 8, 20, 11, 0)),
            status="In Progress",
            name="Test Renter Name",
            phone_number="4168202370",
            deposit_payment_method="Cash",
            items_left_behind=[],
            notes=None,
            return_location=None,
            return_time=None,
        )
        self.service.db_service.get_rentals_on_date.return_value = [summary.model_dump()]

        result = self.service.lookup_rentals_on_date(date=datetime.date(2025, 8, 20))

        self.assertEqual([summary.model_dump(mode="json")], result)
        self.service.db_service.get_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=None, in_progress_rentals_only=False
        )

    def test_lookup_rentals_passes_filters(self):
        self.service.db_service.get_rentals_on_date.return_value = []
        result = self.service.lookup_rentals_on_date(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER, in_progress_only=True
        )
        self.assertEqual([], result)
        self.service.db_service.get_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER, in_progress_rentals_only=True
        )

    def test_lookup_reservations_on_date(self):
        self.service.db_service.get_reservations_on_date.return_value = []
        result = self.service.lookup_reservations_on_date(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.WHEELCHAIR
        )
        self.assertEqual([], result)
        self.service.db_service.get_reservations_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.WHEELCHAIR
        )

    def test_lookup_available_devices(self):
        self.service.db_service.get_available_device_ids.return_value = ["W01", "W02"]
        result = self.service.lookup_available_devices(device_type=DeviceType.WHEELCHAIR, location=Location.BLC)
        self.assertEqual(["W01", "W02"], result)
        self.service.db_service.get_available_device_ids.assert_called_once_with(
            cne_year=2025, device_type=DeviceType.WHEELCHAIR, location=Location.BLC
        )

    def test_lookup_full_inventory_converts_items(self):
        device = Device(
            cne_year=2025, id="W01", type=DeviceType.WHEELCHAIR, status=DeviceStatus.AVAILABLE, location=Location.BLC
        )
        self.service.db_service.get_full_inventory.return_value = [device.model_dump()]
        result = self.service.lookup_full_inventory()
        self.assertEqual([device.model_dump(mode="json")], result)
        self.service.db_service.get_full_inventory.assert_called_once_with(cne_year=2025)

    # ── aggregate tools ───────────────────────────────────────────────────

    def test_count_unreturned_rentals_on_date(self):
        self.service.db_service.get_rentals_on_date.return_value = [{}, {}, {}]
        result = self.service.count_unreturned_rentals_on_date(date=datetime.date(2025, 8, 20))
        self.assertEqual(3, result)
        self.service.db_service.get_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=None, in_progress_rentals_only=True
        )

    def test_count_rentals_on_date(self):
        self.service.db_service.get_rentals_on_date.return_value = [{}, {}]
        result = self.service.count_rentals_on_date(date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER)
        self.assertEqual(2, result)
        self.service.db_service.get_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER
        )

    def test_count_available_devices_by_location(self):
        self.service.db_service.get_available_device_ids.side_effect = lambda cne_year, device_type, location: (
            ["S01", "S02"] if location == Location.BLC else ["S03"]
        )
        result = self.service.count_available_devices_by_location(device_type=DeviceType.SCOOTER)
        self.assertEqual({Location.BLC.value: 2, Location.PG.value: 1}, result)

    def test_reservation_counts_converts_dataframe(self):
        self.service.db_service.get_reservation_count.return_value = pd.DataFrame([
            {"date": "2025-08-20", "device_type": "Scooter", "location": "BLC", "count": 5},
        ])
        result = self.service.reservation_counts()
        self.assertEqual(1, len(result))
        self.assertEqual(5, result[0]["count"])
        self.service.db_service.get_reservation_count.assert_called_once_with(2025)


class TestChatServiceAnswer(TestCase):
    """Tests for the answer() orchestration and history conversion."""

    def test_to_model_messages_maps_roles(self):
        history = [
            ChatMessage(role=ChatRole.USER, content="hello"),
            ChatMessage(role=ChatRole.ASSISTANT, content="hi there"),
        ]
        messages = _to_model_messages(history)
        self.assertEqual(2, len(messages))
        self.assertIsInstance(messages[0], ModelRequest)
        self.assertIsInstance(messages[1], ModelResponse)

    def test_to_model_messages_empty(self):
        self.assertEqual([], _to_model_messages([]))

    def test_answer_uses_agent_and_history(self):
        service = _make_chat_service()
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = MagicMock(output="the answer", **{"new_messages.return_value": []})
        service._agent = mock_agent  # pylint: disable=protected-access

        result = service.answer("how many rentals?", [ChatMessage(role=ChatRole.USER, content="hi")])

        self.assertEqual("the answer", result)
        _, kwargs = mock_agent.run_sync.call_args
        self.assertEqual(1, len(kwargs["message_history"]))

    def test_answer_handles_no_history(self):
        service = _make_chat_service()
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = MagicMock(output="hi", **{"new_messages.return_value": []})
        service._agent = mock_agent  # pylint: disable=protected-access

        self.assertEqual("hi", service.answer("hello"))

    def test_answer_debug_logs_messages_tool_calls_and_responses(self):
        service = _make_chat_service()
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = MagicMock(
            output="There is 1 rental in progress.",
            **{"new_messages.return_value": [
                ModelResponse(parts=[ToolCallPart(tool_name="get_today", args={})]),
                ModelRequest(parts=[ToolReturnPart(tool_name="get_today", content="2026-06-07")]),
                ModelResponse(parts=[TextPart(content="There is 1 rental in progress.")]),
            ]},
        )
        service._agent = mock_agent  # pylint: disable=protected-access

        with self.assertLogs("api.src.chat_service", level="DEBUG") as captured:
            service.answer("how many rentals are in progress today?")

        log_output = "\n".join(captured.output)
        self.assertIn("Chatbot user message: how many rentals are in progress today?", log_output)
        self.assertIn("Chatbot tool call: get_today", log_output)
        self.assertIn("Chatbot tool response: get_today -> 2026-06-07", log_output)
        self.assertIn("Chatbot agent response: There is 1 rental in progress.", log_output)
