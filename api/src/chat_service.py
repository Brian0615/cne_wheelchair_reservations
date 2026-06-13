import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from api.src.dynamodb_service import DynamoDBService
from common.cne_dates import CNEDates
from common.constants import DeviceStatus, DeviceType, Location, PaymentMethod
from common.data_models import (
    ChatMessage,
    ChatRole,
    Device,
    Rental,
    RentalSummary,
    Reservation,
    ReservationCount,
    ReservationStatusCount,
)
from common.logger import initialize_logger
from common.utils import get_default_timezone

logger = initialize_logger()

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
_MANUAL_PATH = Path(__file__).resolve().parent.parent / "assets" / "reservations_manual.md"
_APP_USAGE_GUIDE = _MANUAL_PATH.read_text(encoding="utf-8")

_SYSTEM_PROMPT_TEMPLATE = """\
You are a helpful assistant for staff of the CNE (Canadian National Exhibition) Wheelchair and Scooter \
Reservations application. You help staff look up rental/reservation/device information, answer aggregate \
questions about the current day's operations, and explain how to use the application.

Scope rules:
- Only answer questions about CNE wheelchair/scooter rentals, reservations, devices/inventory, and how to use \
this application.
- For anything outside this scope, briefly decline (e.g. "I can only help with CNE rental, reservation, and \
inventory questions"). Do not attempt to answer out-of-scope questions and do not call any tools for them.
- Always use the provided tools to retrieve live data instead of guessing. Never invent rental IDs, names, \
counts, or availability.
- When a question references a specific rental, reservation, or device ID, prefer the by-ID lookup tools \
(lookup_rental_by_id, lookup_reservation_by_id, lookup_device_by_id) over scanning lists.
- There is no expected-return-time or "due back" data. For "overdue"/"outstanding"/"still out" questions, use \
lookup_outstanding_rentals and make clear you are reporting rentals that have not been returned yet, not overdue ones.
- There is no explicit "no-show" status. Approximate unfulfilled/no-show reservations from reservation_status_counts \
(a reservation whose date has passed but is still Reserved/Confirmed/Pending rather than Picked Up or Completed), and \
note that this is an approximation.
- For fee and deposit amounts, use fee_and_deposit_schedule rather than guessing.
- Be concise. The current CNE year is {cne_year}. When a question refers to today, or fair dates, use the available \
 tool calls to determine the relevant dates.
- When information is asked generally (e.g. "How many rentals today?"), provide overall information as well as \
When asked how to use the application, answer using the App Usage Guide below.

===== APP USAGE GUIDE =====
{app_usage_guide}
===== END APP USAGE GUIDE =====
"""


def _to_model_messages(history: List[ChatMessage]) -> List[ModelMessage]:
    """Convert the conversation history into pydantic-ai message objects."""
    messages: List[ModelMessage] = []
    for message in history:
        if message.role == ChatRole.USER:
            messages.append(ModelRequest(parts=[UserPromptPart(content=message.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=message.content)]))
    return messages


class ChatService:
    """Chatbot service that answers questions about CNE rentals/reservations/inventory.

    The pydantic-ai agent is built lazily so that importing this module (and the chat router) does not
    require a Gemini API key — only an actual call to ``answer`` constructs the agent.
    """

    def __init__(self):
        self.cne_year = CNEDates.get_cne_year()
        self.db_service = DynamoDBService()
        self._agent: Optional[Agent] = None

    # ==============================
    # AGENT SETUP
    # ==============================

    def _system_prompt(self) -> str:
        today = datetime.datetime.now(get_default_timezone()).date()
        fair_start, fair_end = CNEDates.get_cne_start_end_dates()
        return _SYSTEM_PROMPT_TEMPLATE.format(
            cne_year=self.cne_year,
            today=today.isoformat(),
            fair_start=fair_start.date().isoformat(),
            fair_end=fair_end.date().isoformat(),
            app_usage_guide=_APP_USAGE_GUIDE,
        )

    def _build_agent(self) -> Agent:
        model = GoogleModel(
            os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            provider=GoogleProvider(api_key=os.environ["GEMINI_API_KEY"]),
        )
        agent = Agent(model=model, system_prompt=self._system_prompt())

        # register the tools available to the agent
        for tool in (
                self.get_today,
                self.lookup_rentals_on_date,
                self.lookup_reservations_on_date,
                self.lookup_available_devices,
                self.lookup_full_inventory,
                self.lookup_rental_by_id,
                self.lookup_reservation_by_id,
                self.lookup_device_by_id,
                self.lookup_devices_by_status,
                self.lookup_current_rental_for_device,
                self.lookup_outstanding_rentals,
                self.search_reservations,
                self.count_unreturned_rentals_on_date,
                self.count_rentals_on_date,
                self.count_available_devices_by_location,
                self.reservation_counts,
                self.reservation_status_counts,
                self.fee_and_deposit_schedule,
        ):
            agent.tool_plain(tool)

        return agent

    @property
    def agent(self) -> Agent:
        """Lazily build and cache the pydantic-ai agent."""
        if self._agent is None:
            self._agent = self._build_agent()
        return self._agent

    def answer(self, message: str, history: Optional[List[ChatMessage]] = None) -> str:
        """Answer a user message, using the conversation history for context."""
        logger.debug("Chatbot user message: %s", message)
        result = self.agent.run_sync(message, message_history=_to_model_messages(history or []))
        self._log_agent_activity(result)
        return result.output

    @staticmethod
    def _log_agent_activity(result) -> None:
        """Debug-log the agent's tool calls, tool responses, and text responses for this run."""
        for run_message in result.new_messages():
            for part in run_message.parts:
                if isinstance(part, ToolCallPart):
                    logger.debug("Chatbot tool call: %s args=%s", part.tool_name, part.args)
                elif isinstance(part, ToolReturnPart):
                    logger.debug("Chatbot tool response: %s -> %s", part.tool_name, part.content)
                elif isinstance(part, TextPart):
                    logger.debug("Chatbot agent response: %s", part.content)

    # ==============================
    # CONTEXT TOOLS
    # ==============================

    def get_today(self) -> str:
        """Get today's date (in the CNE's local timezone) as an ISO-formatted string (YYYY-MM-DD).

        Use this whenever a question refers to "today", "now", or the current date.
        """
        return datetime.datetime.now(get_default_timezone()).date().isoformat()

    # ==============================
    # LOOKUP TOOLS
    # ==============================

    def lookup_rentals_on_date(
            self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
            in_progress_only: bool = False,
    ) -> List[dict]:
        """Look up rentals on a specific date.

        Args:
            date: The date of the rentals to look up.
            device_type: Optionally restrict to a single device type (Scooter or Wheelchair).
            in_progress_only: If true, only return rentals that have not yet been returned.
        """
        items = self.db_service.get_rentals_on_date(
            date=date, device_type=device_type, in_progress_rentals_only=in_progress_only
        )
        return [RentalSummary(**item).model_dump(mode="json") for item in items]

    def lookup_reservations_on_date(
            self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
    ) -> List[dict]:
        """Look up reservations on a specific date.

        Args:
            date: The date of the reservations to look up.
            device_type: Optionally restrict to a single device type (Scooter or Wheelchair).
        """
        items = self.db_service.get_reservations_on_date(date=date, device_type=device_type)
        return [Reservation(**item).model_dump(mode="json") for item in items]

    def lookup_available_devices(
            self,
            device_type: DeviceType,
            location: Optional[Location] = None,
    ) -> List[str]:
        """List the IDs of devices that are currently available for walk-in rentals.

        Args:
            device_type: The device type to look up (Scooter or Wheelchair).
            location: Optionally restrict to a single pickup location (BLC or PG).
        """
        return self.db_service.get_available_device_ids(
            cne_year=self.cne_year, device_type=device_type, location=location
        )

    def lookup_full_inventory(self) -> List[dict]:
        """List the full device inventory for the current CNE year, including status and location."""
        items = self.db_service.get_full_inventory(cne_year=self.cne_year)
        return [Device(**item).model_dump(mode="json") for item in items]

    def lookup_rental_by_id(self, rental_id: str) -> Optional[dict]:
        """Look up a single rental by its ID (e.g. "W0820001").

        Returns the full rental record — including renter info, payment amounts/methods, items left
        behind, staff names, and return location/time/staff — or None if no such rental exists. Use
        this whenever a question references a specific rental ID.
        """
        item = self.db_service.get_rental_by_id(cne_year=self.cne_year, rental_id=rental_id)
        return Rental(**item).model_dump(mode="json") if item else None

    def lookup_reservation_by_id(self, reservation_id: str) -> Optional[dict]:
        """Look up a single reservation by its ID (e.g. "W0820001").

        Returns the full reservation record — including pickup location, reservation time, status, and
        the linked rental_id (if it has been picked up) — or None if no such reservation exists. Use
        this whenever a question references a specific reservation ID.
        """
        item = self.db_service.get_reservation_by_id(cne_year=self.cne_year, reservation_id=reservation_id)
        return Reservation(**item).model_dump(mode="json") if item else None

    def lookup_device_by_id(self, device_id: str) -> Optional[dict]:
        """Look up a single device by its ID (e.g. "W04") to see its current status and location.

        Returns None if no such device exists. A status of "Rented" means it is currently out on a
        rental; use lookup_current_rental_for_device to find who has it.
        """
        item = self.db_service.get_device_by_id(cne_year=self.cne_year, device_id=device_id)
        return Device(**item).model_dump(mode="json") if item else None

    def lookup_devices_by_status(
            self,
            status: DeviceStatus,
            device_type: Optional[DeviceType] = None,
            location: Optional[Location] = None,
    ) -> List[dict]:
        """List devices that currently have a given status, with their IDs and locations.

        Args:
            status: The device status to filter by (Available, Backup, Out of Service, or Rented).
            device_type: Optionally restrict to a single device type (Scooter or Wheelchair).
            location: Optionally restrict to a single location (BLC or PG).
        """
        items = self.db_service.get_devices_by_status(
            cne_year=self.cne_year, status=status, device_type=device_type, location=location
        )
        return [Device(**item).model_dump(mode="json") for item in items]

    def lookup_current_rental_for_device(self, device_id: str) -> Optional[dict]:
        """Find the in-progress (not yet returned) rental currently on a device.

        Returns the rental record (including who has it) or None if the device is not currently out on
        a rental. Note: there is no expected-return-time tracked, so this cannot say when it is due back.
        """
        item = self.db_service.get_current_rental_for_device(cne_year=self.cne_year, device_id=device_id)
        return Rental(**item).model_dump(mode="json") if item else None

    def lookup_outstanding_rentals(self, device_type: Optional[DeviceType] = None) -> List[dict]:
        """List all rentals that are still in progress (not yet returned) across the whole CNE year.

        Use this for "outstanding"/"not yet returned"/"still out" questions. There is no
        expected-return-time, so these are not necessarily "overdue" — only not-yet-returned.

        Args:
            device_type: Optionally restrict to a single device type (Scooter or Wheelchair).
        """
        items = self.db_service.get_outstanding_rentals(cne_year=self.cne_year, device_type=device_type)
        return [RentalSummary(**item).model_dump(mode="json") for item in items]

    def search_reservations(
            self,
            name: Optional[str] = None,
            phone_number: Optional[str] = None,
    ) -> List[dict]:
        """Search reservations for the current CNE year by renter name and/or phone number.

        Provide at least one of name (matched as a case-sensitive substring) or phone_number (exact
        match). Returns matching reservations across all dates. Use this to answer "does <person> have
        a reservation?".
        """
        items = self.db_service.search_reservations(
            cne_year=self.cne_year, name=name, phone_number=phone_number
        )
        return [Reservation(**item).model_dump(mode="json") for item in items]

    # ==============================
    # AGGREGATE TOOLS
    # ==============================

    def count_unreturned_rentals_on_date(
            self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
    ) -> int:
        """Count rentals on a date that have not yet been returned (still in progress).

        Args:
            date: The date to count unreturned rentals for.
            device_type: Optionally restrict to a single device type (Scooter or Wheelchair).
        """
        return self.db_service.count_rentals_on_date(
            date=date, device_type=device_type, in_progress_rentals_only=True
        )

    def count_rentals_on_date(
            self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
    ) -> int:
        """Count the total number of rentals on a date.

        Args:
            date: The date to count rentals for.
            device_type: Optionally restrict to a single device type (Scooter or Wheelchair).
        """
        return self.db_service.count_rentals_on_date(date=date, device_type=device_type)

    def count_available_devices_by_location(self, device_type: DeviceType) -> Dict[str, int]:
        """Count how many devices of a type are available for walk-in rentals at each location.

        Args:
            device_type: The device type to count (Scooter or Wheelchair).
        """
        return self.db_service.count_available_devices_by_location(
            cne_year=self.cne_year, device_type=device_type
        )

    def reservation_counts(self) -> List[dict]:
        """Get reservation counts broken down by date, device type, and location for the current CNE year."""
        counts = self.db_service.get_reservation_count(self.cne_year)
        return [ReservationCount(**row).model_dump(mode="json") for row in counts.to_dict(orient="records")]

    def reservation_status_counts(self) -> List[dict]:
        """Get reservation counts broken down by status and device type for the current CNE year.

        Includes every status (Pending Confirmation, Confirmed, Reserved, Picked Up, Completed,
        Cancelled, Waitlisted). There is no explicit "no-show" status: a no-show / unfulfilled
        reservation can be approximated as one whose date has passed but is still in a pre-pickup
        status (Reserved/Confirmed/Pending) rather than Picked Up or Completed.
        """
        counts = self.db_service.get_reservation_status_counts(self.cne_year)
        return [ReservationStatusCount(**row).model_dump(mode="json") for row in counts.to_dict(orient="records")]

    def fee_and_deposit_schedule(self) -> dict:
        """Get the rental fee and refundable deposit amounts (in CAD) for each device type, plus the
        accepted payment methods. This is fixed reference data, not live database data.
        """
        return {
            "fees_and_deposits": {
                device_type.value: {
                    "rental_fee": DeviceType.get_fee_amount(device_type),
                    "deposit": DeviceType.get_deposit_amount(device_type),
                }
                for device_type in DeviceType
            },
            "accepted_fee_payment_methods": sorted(PaymentMethod.get_accepted_fee_payment_methods()),
            "accepted_deposit_payment_methods": sorted(PaymentMethod.get_accepted_deposit_payment_methods()),
        }
