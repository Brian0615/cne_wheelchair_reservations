import datetime
import re
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pandas as pd
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, ToolCallPart, ToolReturnPart

from pydantic_ai import ModelHTTPError

from api.src.chat_service import GEMINI_MODEL_FALLBACK_CHAIN, ChatService, _to_model_messages
from common.cne_dates import CNEDates
from common.constants import DeviceStatus, DeviceType, Location, PaymentMethod, ReservationStatus
from common.data_models import ChatMessage, ChatRole, Device, Rental, RentalSummary, Reservation
from common.utils import get_default_timezone


def _make_chat_service() -> ChatService:
    """Create a ChatService with a mocked DynamoDBService (no real AWS / agent involved).

    The model fallback chain is set explicitly (rather than relying on `ChatService.__init__` reading
    `GEMINI_MODEL` from the environment) so these tests behave the same regardless of the local shell's
    environment variables.
    """
    service = ChatService()
    service.db_service = MagicMock()
    service.cne_year = 2025
    service._model_names = GEMINI_MODEL_FALLBACK_CHAIN  # pylint: disable=protected-access
    service._current_model_index = 0  # pylint: disable=protected-access
    service._agents = {}  # pylint: disable=protected-access
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


def _make_rental_summary(**overrides) -> RentalSummary:
    """Build a full RentalSummary for tests."""
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
        "deposit_payment_method": "Cash",
        "deposit_payment_amount": 50,
        "items_left_behind": [],
        "notes": None,
        "return_location": None,
        "return_time": None,
    }
    params.update(overrides)
    return RentalSummary(**params)


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

    # ── context tools ──────────────────────────────────

    def test_get_today_returns_iso_date(self):
        today = datetime.datetime.now(get_default_timezone()).date().isoformat()
        self.assertEqual(self.service.get_today(), today)

    def test_get_usage_guide_returns_manual_text(self):
        from api.src.chat_service import _APP_USAGE_GUIDE  # pylint: disable=import-outside-toplevel

        self.assertEqual(self.service.get_usage_guide(), _APP_USAGE_GUIDE)

    # ── lookup tools ────────────────────────────────────

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
            deposit_payment_amount=50,
            items_left_behind=[],
            notes=None,
            return_location=None,
            return_time=None,
        )
        self.service.db_service.get_rentals_on_date.return_value = [summary.model_dump()]

        result = self.service.lookup_rentals_on_date(date=datetime.date(2025, 8, 20))

        self.assertEqual(result, [summary.model_dump(mode="json")])
        self.service.db_service.get_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=None, in_progress_rentals_only=False
        )

    def test_lookup_rentals_passes_filters(self):
        summary = _make_rental_summary()
        self.service.db_service.get_rentals_on_date.return_value = [summary.model_dump()]
        result = self.service.lookup_rentals_on_date(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER, in_progress_only=True
        )
        self.assertEqual(result, [summary.model_dump(mode="json")])
        self.service.db_service.get_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER, in_progress_rentals_only=True
        )

    def test_lookup_rentals_on_date_reports_no_data_instead_of_empty_list(self):
        self.service.db_service.get_rentals_on_date.return_value = []
        result = self.service.lookup_rentals_on_date(date=datetime.date(2025, 8, 20))
        self.assertIsInstance(result, str)
        self.assertIn("2025-08-20", result)

    def test_lookup_reservations_on_date(self):
        reservation = _make_reservation()
        self.service.db_service.get_reservations_on_date.return_value = [reservation.model_dump()]
        result = self.service.lookup_reservations_on_date(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.WHEELCHAIR
        )
        self.assertEqual(result, [reservation.model_dump(mode="json")])
        self.service.db_service.get_reservations_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.WHEELCHAIR
        )

    def test_lookup_reservations_on_date_reports_no_data_instead_of_empty_list(self):
        self.service.db_service.get_reservations_on_date.return_value = []
        result = self.service.lookup_reservations_on_date(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.WHEELCHAIR
        )
        self.assertIsInstance(result, str)
        self.assertIn("2025-08-20", result)

    def test_lookup_available_devices(self):
        self.service.db_service.get_available_device_ids.return_value = ["W01", "W02"]
        result = self.service.lookup_available_devices(device_type=DeviceType.WHEELCHAIR, location=Location.BLC)
        self.assertEqual(result, ["W01", "W02"])
        self.service.db_service.get_available_device_ids.assert_called_once_with(
            cne_year=2025, device_type=DeviceType.WHEELCHAIR, location=Location.BLC
        )

    def test_lookup_available_devices_reports_no_data_instead_of_empty_list(self):
        self.service.db_service.get_available_device_ids.return_value = []
        result = self.service.lookup_available_devices(device_type=DeviceType.WHEELCHAIR)
        self.assertIsInstance(result, str)

    def test_lookup_full_inventory_converts_items(self):
        device = Device(
            cne_year=2025, id="W01", type=DeviceType.WHEELCHAIR, status=DeviceStatus.AVAILABLE, location=Location.BLC
        )
        self.service.db_service.get_full_inventory.return_value = [device.model_dump()]
        result = self.service.lookup_full_inventory()
        self.assertEqual(result, [device.model_dump(mode="json")])
        self.service.db_service.get_full_inventory.assert_called_once_with(cne_year=2025)

    def test_lookup_full_inventory_reports_no_data_instead_of_empty_list(self):
        self.service.db_service.get_full_inventory.return_value = []
        result = self.service.lookup_full_inventory()
        self.assertIsInstance(result, str)

    def test_lookup_rental_by_id_converts_item(self):
        rental = _make_rental()
        self.service.db_service.get_rental_by_id.return_value = rental.model_dump()
        result = self.service.lookup_rental_by_id(rental_id="W0820001")
        self.assertEqual(result, rental.model_dump(mode="json"))
        self.service.db_service.get_rental_by_id.assert_called_once_with(cne_year=2025, rental_id="W0820001")

    def test_lookup_rental_by_id_not_found(self):
        self.service.db_service.get_rental_by_id.return_value = None
        self.assertIsNone(self.service.lookup_rental_by_id(rental_id="W0820099"))

    def test_lookup_reservation_by_id_converts_item(self):
        reservation = _make_reservation()
        self.service.db_service.get_reservation_by_id.return_value = reservation.model_dump()
        result = self.service.lookup_reservation_by_id(reservation_id="W0820001")
        self.assertEqual(result, reservation.model_dump(mode="json"))
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
        self.assertEqual(result, device.model_dump(mode="json"))
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
        self.assertEqual(result, [device.model_dump(mode="json")])
        self.service.db_service.get_devices_by_status.assert_called_once_with(
            cne_year=2025, status=DeviceStatus.OUT_OF_SERVICE, device_type=DeviceType.WHEELCHAIR, location=Location.PG
        )

    def test_lookup_devices_by_status_reports_no_data_instead_of_empty_list(self):
        self.service.db_service.get_devices_by_status.return_value = []
        result = self.service.lookup_devices_by_status(status=DeviceStatus.OUT_OF_SERVICE)
        self.assertIsInstance(result, str)

    def test_lookup_current_rental_for_device_converts_item(self):
        rental = _make_rental()
        self.service.db_service.get_current_rental_for_device.return_value = rental.model_dump()
        result = self.service.lookup_current_rental_for_device(device_id="W01")
        self.assertEqual(result, rental.model_dump(mode="json"))
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
            deposit_payment_amount=50,
            items_left_behind=[],
            notes=None,
            return_location=None,
            return_time=None,
        )
        self.service.db_service.get_outstanding_rentals.return_value = [summary.model_dump()]
        result = self.service.lookup_outstanding_rentals(device_type=DeviceType.WHEELCHAIR)
        self.assertEqual(result, [summary.model_dump(mode="json")])
        self.service.db_service.get_outstanding_rentals.assert_called_once_with(
            cne_year=2025, device_type=DeviceType.WHEELCHAIR
        )

    def test_lookup_outstanding_rentals_reports_no_data_instead_of_empty_list(self):
        self.service.db_service.get_outstanding_rentals.return_value = []
        result = self.service.lookup_outstanding_rentals()
        self.assertIsInstance(result, str)

    def test_search_reservations_converts_items(self):
        reservation = _make_reservation()
        self.service.db_service.search_reservations.return_value = [reservation.model_dump()]
        result = self.service.search_reservations(name="Test", phone_number="4168202370")
        self.assertEqual(result, [reservation.model_dump(mode="json")])
        self.service.db_service.search_reservations.assert_called_once_with(
            cne_year=2025, name="Test", phone_number="4168202370"
        )

    def test_search_reservations_reports_no_data_instead_of_empty_list(self):
        self.service.db_service.search_reservations.return_value = []
        result = self.service.search_reservations(name="Nobody")
        self.assertIsInstance(result, str)

    # ── aggregate tools ────────────────────────────────

    def test_count_unreturned_rentals_on_date(self):
        self.service.db_service.count_rentals_on_date.return_value = 3
        result = self.service.count_unreturned_rentals_on_date(date=datetime.date(2025, 8, 20))
        self.assertEqual(result, 3)
        self.service.db_service.count_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=None, in_progress_rentals_only=True
        )

    def test_count_rentals_on_date(self):
        self.service.db_service.count_rentals_on_date.return_value = 2
        result = self.service.count_rentals_on_date(date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER)
        self.assertEqual(result, 2)
        self.service.db_service.count_rentals_on_date.assert_called_once_with(
            date=datetime.date(2025, 8, 20), device_type=DeviceType.SCOOTER
        )

    def test_count_available_devices_by_location(self):
        self.service.db_service.count_available_devices_by_location.return_value = {
            Location.BLC.value: 2, Location.PG.value: 1
        }
        result = self.service.count_available_devices_by_location(device_type=DeviceType.SCOOTER)
        self.assertEqual(result, {Location.BLC.value: 2, Location.PG.value: 1})
        self.service.db_service.count_available_devices_by_location.assert_called_once_with(
            cne_year=2025, device_type=DeviceType.SCOOTER
        )

    def test_reservation_counts_converts_dataframe(self):
        self.service.db_service.get_reservation_count.return_value = pd.DataFrame([
            {"date": "2025-08-20", "device_type": "Scooter", "location": "BLC", "count": 5},
        ])
        result = self.service.reservation_counts()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["count"], 5)
        self.service.db_service.get_reservation_count.assert_called_once_with(2025)

    def test_reservation_counts_reports_no_data_instead_of_empty_list(self):
        self.service.db_service.get_reservation_count.return_value = pd.DataFrame(
            columns=["date", "device_type", "location", "count"]
        )
        result = self.service.reservation_counts()
        self.assertIsInstance(result, str)

    def test_reservation_status_counts_converts_dataframe(self):
        self.service.db_service.get_reservation_status_counts.return_value = pd.DataFrame([
            {"status": "Reserved", "device_type": "Wheelchair", "count": 3},
            {"status": "Picked Up", "device_type": "Scooter", "count": 2},
        ])
        result = self.service.reservation_status_counts()
        self.assertEqual(len(result), 2)
        self.assertEqual({row["status"] for row in result}, {"Reserved", "Picked Up"})
        self.service.db_service.get_reservation_status_counts.assert_called_once_with(2025)

    def test_reservation_status_counts_reports_no_data_instead_of_empty_list(self):
        self.service.db_service.get_reservation_status_counts.return_value = pd.DataFrame(
            columns=["status", "device_type", "count"]
        )
        result = self.service.reservation_status_counts()
        self.assertIsInstance(result, str)

    def test_fee_and_deposit_schedule_is_static(self):
        result = self.service.fee_and_deposit_schedule()
        self.assertEqual(result["fees_and_deposits"]["Scooter"]["rental_fee"], 45)
        self.assertEqual(result["fees_and_deposits"]["Scooter"]["deposit"], 100)
        self.assertEqual(result["fees_and_deposits"]["Wheelchair"]["rental_fee"], 20)
        self.assertEqual(result["fees_and_deposits"]["Wheelchair"]["deposit"], 50)
        self.assertIn(PaymentMethod.CASH, result["accepted_fee_payment_methods"])
        self.service.db_service.assert_not_called()


class TestChatServiceSystemPrompt(TestCase):
    """Tests for system prompt construction."""

    def setUp(self):
        self.service = _make_chat_service()

    def test_system_prompt_includes_cne_year_and_fair_dates(self):
        fair_start, fair_end = CNEDates.get_cne_start_end_dates()
        prompt = self.service._system_prompt()  # pylint: disable=protected-access
        self.assertIn(str(self.service.cne_year), prompt)
        self.assertIn(fair_start.date().isoformat(), prompt)
        self.assertIn(fair_end.date().isoformat(), prompt)

    def test_system_prompt_references_usage_guide_tool_instead_of_inlining_it(self):
        """The guide is fetched on demand via get_usage_guide, not resent on every model call."""
        prompt = self.service._system_prompt()  # pylint: disable=protected-access
        self.assertIn("get_usage_guide", prompt)
        self.assertNotIn("===== APP USAGE GUIDE =====", prompt)

    def test_system_prompt_does_not_bake_in_todays_date(self):
        """The agent is cached, so today's date must come from get_today rather than the prompt."""
        fair_start, fair_end = CNEDates.get_cne_start_end_dates()
        prompt = self.service._system_prompt()  # pylint: disable=protected-access

        # the fair start/end are the only dates that may legitimately be hard-coded into the prompt
        dates_in_prompt = set(re.findall(r"\d{4}-\d{2}-\d{2}", prompt))
        self.assertEqual(dates_in_prompt, {fair_start.date().isoformat(), fair_end.date().isoformat()})
        self.assertIn("get_today", prompt)

    def test_get_usage_guide_survives_braces_in_manual(self):
        """Braces in the manual must not break tool output (the guide is not .format()-ed)."""
        guide_text = 'Set {"limit": 5} in the {config} field.'
        with patch("api.src.chat_service._APP_USAGE_GUIDE", guide_text):
            result = self.service.get_usage_guide()
        self.assertEqual(result, guide_text)


class TestChatServiceAnswer(TestCase):
    """Tests for the answer() orchestration and history conversion."""

    def test_to_model_messages_maps_roles(self):
        history = [
            ChatMessage(role=ChatRole.USER, content="hello"),
            ChatMessage(role=ChatRole.ASSISTANT, content="hi there"),
        ]
        messages = _to_model_messages(history)
        self.assertEqual(len(messages), 2)
        self.assertIsInstance(messages[0], ModelRequest)
        self.assertIsInstance(messages[1], ModelResponse)

    def test_to_model_messages_empty(self):
        self.assertEqual(_to_model_messages([]), [])

    @staticmethod
    def _mock_usage(input_tokens=10, output_tokens=5, cache_read_tokens=0, cache_write_tokens=0):
        """Build a mock `RunUsage`-like object with a working `total_tokens` property."""
        usage = MagicMock(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
        )
        usage.total_tokens = input_tokens + output_tokens
        return usage

    def test_answer_uses_agent_and_history(self):
        service = _make_chat_service()
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = MagicMock(
            output="the answer",
            usage=self._mock_usage(input_tokens=100, output_tokens=20),
            **{"new_messages.return_value": []},
        )
        service._agents = {GEMINI_MODEL_FALLBACK_CHAIN[0]: mock_agent}  # pylint: disable=protected-access

        result = service.answer("how many rentals?", [ChatMessage(role=ChatRole.USER, content="hi")])

        self.assertEqual(result.answer, "the answer")
        self.assertEqual(result.model, GEMINI_MODEL_FALLBACK_CHAIN[0])
        self.assertEqual(result.input_tokens, 100)
        self.assertEqual(result.output_tokens, 20)
        self.assertEqual(result.cache_read_tokens, 0)
        self.assertEqual(result.total_tokens, 120)
        _, kwargs = mock_agent.run_sync.call_args
        self.assertEqual(len(kwargs["message_history"]), 1)

    def test_answer_handles_no_history(self):
        service = _make_chat_service()
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = MagicMock(
            output="hi", usage=self._mock_usage(), **{"new_messages.return_value": []}
        )
        service._agents = {GEMINI_MODEL_FALLBACK_CHAIN[0]: mock_agent}  # pylint: disable=protected-access

        self.assertEqual(service.answer("hello").answer, "hi")

    def test_answer_debug_logs_messages_tool_calls_responses_and_usage(self):
        service = _make_chat_service()
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = MagicMock(
            output="There is 1 rental in progress.",
            usage=self._mock_usage(input_tokens=200, output_tokens=15, cache_read_tokens=50, cache_write_tokens=0),
            **{"new_messages.return_value": [
                ModelResponse(parts=[ToolCallPart(tool_name="get_today", args={})]),
                ModelRequest(parts=[ToolReturnPart(tool_name="get_today", content="2026-06-07")]),
                ModelResponse(parts=[TextPart(content="There is 1 rental in progress.")]),
            ]},
        )
        service._agents = {GEMINI_MODEL_FALLBACK_CHAIN[0]: mock_agent}  # pylint: disable=protected-access

        with self.assertLogs("api.src.chat_service", level="DEBUG") as captured:
            service.answer("how many rentals are in progress today?")

        log_output = "\n".join(captured.output)
        self.assertIn("Chatbot user message: how many rentals are in progress today?", log_output)
        self.assertIn("Chatbot tool call: get_today", log_output)
        self.assertIn("Chatbot tool response: get_today -> 2026-06-07", log_output)
        self.assertIn("Chatbot agent response: There is 1 rental in progress.", log_output)
        self.assertIn(
            f"Chatbot response: model={GEMINI_MODEL_FALLBACK_CHAIN[0]} input_tokens=200 output_tokens=15 "
            "cache_read_tokens=50 cache_write_tokens=0",
            log_output,
        )

    def test_answer_resets_to_first_model_for_a_new_conversation(self):
        """A fresh (empty-history) conversation always starts at the first model in the chain, even if a
        prior conversation had fallen back to a later one."""
        service = _make_chat_service()
        service._current_model_index = 2  # pylint: disable=protected-access
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = MagicMock(
            output="hi", usage=self._mock_usage(), **{"new_messages.return_value": []}
        )
        service._agents = {GEMINI_MODEL_FALLBACK_CHAIN[0]: mock_agent}  # pylint: disable=protected-access

        result = service.answer("hello")

        self.assertEqual(result.model, GEMINI_MODEL_FALLBACK_CHAIN[0])
        self.assertEqual(service._current_model_index, 0)  # pylint: disable=protected-access

    def test_answer_falls_back_to_next_model_on_rate_limit(self):
        """If the current model's rate limit is hit, the next model in the chain should be tried."""
        service = _make_chat_service()
        rate_limited_agent = MagicMock()
        rate_limited_agent.run_sync.side_effect = ModelHTTPError(
            status_code=429, model_name=GEMINI_MODEL_FALLBACK_CHAIN[0]
        )
        healthy_agent = MagicMock()
        healthy_agent.run_sync.return_value = MagicMock(
            output="ok", usage=self._mock_usage(), **{"new_messages.return_value": []}
        )
        service._agents = {  # pylint: disable=protected-access
            GEMINI_MODEL_FALLBACK_CHAIN[0]: rate_limited_agent,
            GEMINI_MODEL_FALLBACK_CHAIN[1]: healthy_agent,
        }

        result = service.answer("hello")

        self.assertEqual(result.model, GEMINI_MODEL_FALLBACK_CHAIN[1])
        self.assertEqual(service._current_model_index, 1)  # pylint: disable=protected-access
        rate_limited_agent.run_sync.assert_called_once()
        healthy_agent.run_sync.assert_called_once()

    def test_answer_wraps_around_after_the_last_model_is_rate_limited(self):
        """After the last model in the chain hits its limit, the rotation should wrap back to the first."""
        service = _make_chat_service()
        service._current_model_index = len(GEMINI_MODEL_FALLBACK_CHAIN) - 1  # pylint: disable=protected-access
        rate_limited_agent = MagicMock()
        rate_limited_agent.run_sync.side_effect = ModelHTTPError(
            status_code=429, model_name=GEMINI_MODEL_FALLBACK_CHAIN[-1]
        )
        healthy_agent = MagicMock()
        healthy_agent.run_sync.return_value = MagicMock(
            output="ok", usage=self._mock_usage(), **{"new_messages.return_value": []}
        )
        service._agents = {  # pylint: disable=protected-access
            GEMINI_MODEL_FALLBACK_CHAIN[-1]: rate_limited_agent,
            GEMINI_MODEL_FALLBACK_CHAIN[0]: healthy_agent,
        }

        result = service.answer("hello", [ChatMessage(role=ChatRole.USER, content="hi")])

        self.assertEqual(result.model, GEMINI_MODEL_FALLBACK_CHAIN[0])
        self.assertEqual(service._current_model_index, 0)  # pylint: disable=protected-access

    def test_answer_raises_when_every_model_is_rate_limited(self):
        """If every model in the chain is rate-limited, the last error should propagate."""
        service = _make_chat_service()
        service._agents = {  # pylint: disable=protected-access
            name: MagicMock(run_sync=MagicMock(side_effect=ModelHTTPError(status_code=429, model_name=name)))
            for name in GEMINI_MODEL_FALLBACK_CHAIN
        }

        with self.assertRaises(ModelHTTPError):
            service.answer("hello")

    def test_answer_reraises_non_rate_limit_errors_without_falling_back(self):
        """A non-429 error should propagate immediately rather than triggering model fallback."""
        service = _make_chat_service()
        failing_agent = MagicMock()
        failing_agent.run_sync.side_effect = ModelHTTPError(status_code=500, model_name=GEMINI_MODEL_FALLBACK_CHAIN[0])
        service._agents = {GEMINI_MODEL_FALLBACK_CHAIN[0]: failing_agent}  # pylint: disable=protected-access

        with self.assertRaises(ModelHTTPError):
            service.answer("hello")
        self.assertEqual(service._current_model_index, 0)  # pylint: disable=protected-access
