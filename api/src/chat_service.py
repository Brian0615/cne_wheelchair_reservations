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
from common.constants import DeviceType, Location
from common.data_models import ChatMessage, ChatRole, Device, RentalSummary, Reservation, ReservationCount
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
- Be concise. The current CNE year is {cne_year}. When a question refers to today, or fair dates, use the available \
 tool calls to determine the relevant dates.

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
                self.count_unreturned_rentals_on_date,
                self.count_rentals_on_date,
                self.count_available_devices_by_location,
                self.reservation_counts,
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
        items = self.db_service.get_rentals_on_date(
            date=date, device_type=device_type, in_progress_rentals_only=True
        )
        return len(items)

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
        items = self.db_service.get_rentals_on_date(date=date, device_type=device_type)
        return len(items)

    def count_available_devices_by_location(self, device_type: DeviceType) -> Dict[str, int]:
        """Count how many devices of a type are available for walk-in rentals at each location.

        Args:
            device_type: The device type to count (Scooter or Wheelchair).
        """
        return {
            location.value: len(
                self.db_service.get_available_device_ids(
                    cne_year=self.cne_year, device_type=device_type, location=location
                )
            )
            for location in Location
        }

    def reservation_counts(self) -> List[dict]:
        """Get reservation counts broken down by date, device type, and location for the current CNE year."""
        counts = self.db_service.get_reservation_count(self.cne_year)
        return [ReservationCount(**row).model_dump(mode="json") for row in counts.to_dict(orient="records")]
