import datetime
from unittest import TestCase
from unittest.mock import MagicMock

import pandas as pd
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, ToolCallPart, ToolReturnPart

from api.src.chat_service import ChatService, _to_model_messages
from common.constants import DeviceStatus, DeviceType, Location, PaymentMethod, ReservationStatus
from common.data_models import ChatMessage, ChatRole, Device, Rental, RentalSummary, Reservation
from common.utils import get_default_timezone


def _make_chat_service() -> ChatService:
    """Create a ChatService with a mocked DynamoDBService (no real AWS / agent involved)."""
    service = ChatService()
    service.db_service = MagicMock()
    service.cne_year = 2025
    return service


def _make_rental(**overrides) -> Rental:
    """Build a full Rental for tests."""
    params = {
        "cne_year": 2025,
        "id": "W0820001",
        "date": datetime.date(2025, 8, 20),
        "device_id": "W01",
        "device_type": DeviceType.WHEELCHAIR,
        "reservation_id": "W0820001",
        "pickup_location": Location.BLC,
        "pickup_time": get_default_timezone().localize(datetime.datetime(2025, 8, 20, 11, 0)),
        "status": "In Progress",
        "name": "Test Renter Name",
        "phone_number": "4168202370",
        "address": "1234 Test St",
        "city": "Test City",
        "province": "Ontario",
        "postal_code": "A1B2C3",
        "country": "CAN",
        "fee_payment_amount": 20,
        "fee_payment_method": PaymentMethod.CASH,
        "deposit_payment_amount": 50,
        "deposit_payment_method": PaymentMethod.CASH,
        "items_left_behind": [],
        "notes": None,
        "staff_name": "Test Staff",
        "return_location": None,
        "return_time": None,
        "return_staff_name": None,
    }
    params.update(overrides)
    return Rental(**params)


def _make_reservation(**overrides) -> Reservation:
    """Build a full Reservation for tests."""
    params = {
        "cne_year": 2025,
        "id": "W0820001",
        "date": datetime.date(2025, 8, 20),
        "device_type": DeviceType.WHEELCHAIR,
        "location": Location.BLC,
        "reservation_time": get_default_timezone().localize(datetime.datetime(2025, 8, 20, 11, 0)),
        "name": "Test Reservation Name",
        "phone_number": "4168202370",
        "notes": "N/A",
        "status": ReservationStatus.RESERVED,
    }
    params.update(overrides)
    return Reservation(**params)


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

    def test_lookup_rental_by_id_converts_item(self):
        rental = _make_rental()
        self.service.db_service.get_rental_by_id.return_value = rental.model_dump()
        result = self.service.lookup_rental_by_id(rental_id="W0820001")
        self.assertEqual(rental.model_dump(mode="json"), result)
        self.service.db_service.get_rental_by_id.assert_called_once_with(cne_year=2025, rental_id="W0820001")

    def test_lookup_rental_by_id_not_found(self):
        self.service.db_service.get_rental_by_id.return_value = None
        self.assertIsNone(self.service.lookup_rental_by_id(rental_id="W0820099"))

    def test_lookup_reservation_by_id_converts_item(self):
        reservation = _make_reservation()
        self.service.db_service.get_reservation_by_id.return_value = reservation.model_dump()
        result = self.service.lookup_reservation_by_id(reservation_id="W0820001")
        self.assertEqual(reservation.model_dump(mode="json"), result)
        self.service.db_service.get_reservation_by_id.assert_called_once_with(
            cne_year=2025, reservation_id="W0820001"
        )

    def test_lookup_reservation_by_id_not_found(self):
        self.service.db_service.get_reservation_by_id.return_value = None
        self.assertIsNone(self.service.lookup_reservation_by_id(reservation_id="W0820099"))

    def test_lookup_device_by_id_converts_item(self):
        device = Device(
            cne_year=2025, id="W04", type=DeviceType.WHEELCHAIR, status=DeviceStatus.RENTED, location=Location.BLC
        )
        self.service.db_service.get_device_by_id.return_value = device.model_dump()
        result = self.service.lookup_device_by_id(device_id="W04")
        self.assertEqual(device.model_dump(mode="json"), result)
        self.service.db_service.get_device_by_id.assert_called_once_with(cne_year=2025, device_id="W04")

    def test_lookup_device_by_id_not_found(self):
        self.service.db_service.get_device_by_id.return_value = None
        self.assertIsNone(self.service.lookup_device_by_id(device_id="W99"))

    def test_lookup_devices_by_status_converts_items(self):
        device = Device(
            cne_year=2025, id="W02", type=DeviceType.WHEELCHAIR, status=DeviceStatus.OUT_OF_SERVICE,
            location=Location.PG,
        )
        self.service.db_service.get_devices_by_status.return_value = [device.model_dump()]
        result = self.service.lookup_devices_by_status(
            status=DeviceStatus.OUT_OF_SERVICE, device_type=DeviceType.WHEELCHAIR, location=Location.PG
        )
        self.assertEqual([device.model_dump(mode="json")], result)
        self.service.db_service.get_devices_by_status.assert_called_once_with(
            cne_year=2025, status=DeviceStatus.OUT_OF_SERVICE, device_type=DeviceType.WHEELCHAIR, location=Location.PG
        )

    def test_lookup_current_rental_for_device_converts_item(self):
        rental = _make_rental()
        self.service.db_service.get_current_rental_for_device.return_value = rental.model_dump()
        result = self.service.lookup_current_rental_for_device(device_id="W01")
        self.assertEqual(rental.model_dump(mode="json"), result)
        self.service.db_service.get_current_rental_for_device.assert_called_once_with(
            cne_year=2025, device_id="W01"
        )

    def test_lookup_current_rental_for_device_none(self):
        self.service.db_service.get_current_rental_for_device.return_value = None
        self.assertIsNone(self.service.lookup_current_rental_for_device(device_id="W01"))

    def test_lookup_outstanding_rentals_converts_items(self):
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
        self.service.db_service.get_outstanding_rentals.return_value = [summary.model_dump()]
        result = self.service.lookup_outstanding_rentals(device_type=DeviceType.WHEELCHAIR)
        self.assertEqual([summary.model_dump(mode="json")], result)
        self.service.db_service.get_outstanding_rentals.assert_called_once_with(
            cne_year=2025, device_type=DeviceType.WHEELCHAIR
        )

    def test_search_reservations_converts_items(self):
        reservation = _make_reservation()
        self.service.db_service.search_reservations.return_value = [reservation.model_dump()]
        result = self.service.search_reservations(name="Test", phone_number="4168202370")
        self.assertEqual([reservation.model_dump(mode="json")], result)
        self.service.db_service.search_reservations.assert_called_once_with(
            cne_year=2025, name="Test", phone_number="4168202370"
        )

    # ── aggregate tools ───────────────────────────────────────────────────

    def test_count_unreturned_rentals_on_date(self):
        self.service.db_service.count_rentals_on_date.return_value = 3
        result = self.service.count_unreturned_rentals_on_date(date=datetime.date(2025, 8, 20))
        self.assertEqual(3, result)
        self.service.db_service.count_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=None, in_progress_rentals_only=True
        )

    def test_count_rentals_on_date(self):
        self.service.db_service.count_rentals_on_date.return_value = 2
        result = self.service.count_rentals_on_date(date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER)
        self.assertEqual(2, result)
        self.service.db_service.count_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER
        )

    def test_count_available_devices_by_location(self):
        self.service.db_service.count_available_devices_by_location.return_value = {
            Location.BLC.value: 2, Location.PG.value: 1
        }
        result = self.service.count_available_devices_by_location(device_type=DeviceType.SCOOTER)
        self.assertEqual({Location.BLC.value: 2, Location.PG.value: 1}, result)
        self.service.db_service.count_available_devices_by_location.assert_called_once_with(
            cne_year=2025, device_type=DeviceType.SCOOTER
        )

    def test_reservation_counts_converts_dataframe(self):
        self.service.db_service.get_reservation_count.return_value = pd.DataFrame([
            {"date": "2025-08-20", "device_type": "Scooter", "location": "BLC", "count": 5},
        ])
        result = self.service.reservation_counts()
        self.assertEqual(1, len(result))
        self.assertEqual(5, result[0]["count"])
        self.service.db_service.get_reservation_count.assert_called_once_with(2025)

    def test_reservation_status_counts_converts_dataframe(self):
        self.service.db_service.get_reservation_status_counts.return_value = pd.DataFrame([
            {"status": "Reserved", "device_type": "Wheelchair", "count": 3},
            {"status": "Picked Up", "device_type": "Scooter", "count": 2},
        ])
        result = self.service.reservation_status_counts()
        self.assertEqual(2, len(result))
        self.assertEqual({"Reserved", "Picked Up"}, {row["status"] for row in result})
        self.service.db_service.get_reservation_status_counts.assert_called_once_with(2025)

    def test_fee_and_deposit_schedule_is_static(self):
        result = self.service.fee_and_deposit_schedule()
        self.assertEqual(45, result["fees_and_deposits"]["Scooter"]["rental_fee"])
        self.assertEqual(100, result["fees_and_deposits"]["Scooter"]["deposit"])
        self.assertEqual(20, result["fees_and_deposits"]["Wheelchair"]["rental_fee"])
        self.assertEqual(50, result["fees_and_deposits"]["Wheelchair"]["deposit"])
        self.assertIn(PaymentMethod.CASH, result["accepted_fee_payment_methods"])
        self.service.db_service.assert_not_called()


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
