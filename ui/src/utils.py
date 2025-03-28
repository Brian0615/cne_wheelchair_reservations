from datetime import date, datetime, time
from functools import wraps
from typing import List, Optional, Tuple

import streamlit as st
from pydantic import BaseModel, ValidationError

from common.utils import get_default_timezone
from ui.src.constants import CNEDates
from ui.src.data_service import DataService


def display_validation_errors(errors: List[dict], validation_class: type[BaseModel]):
    """Display validation errors on the UI."""
    display_errors = []
    for error in errors:
        field_name = validation_class.model_fields[error['loc'][0]].title
        if not field_name:
            field_name = error['loc'][0]

        match error['type']:
            case "enum":
                message = error["msg"].replace("Input should be", "Input should be one of:")
            case "string_too_short" | "string_too_long":
                message = error["msg"].replace("String", "Input")
            case _:
                message = error["msg"]
        display_errors.append(f"{field_name}: {message}")

    error_str = "**Validation Error:** There was an error validating the input data. Please check the following fields:"
    error_str = "\n* ".join([error_str] + display_errors)

    st.error(error_str)


def get_date_input(label: str, key_prefix: str, col=None):
    """Get a date input with the default date set to today."""
    all_dates = CNEDates.get_cne_date_list()
    if col is None:
        col, _ = st.columns([1, 3])
    if st.session_state.get(f"{key_prefix}_date") is None:
        st.session_state[f"{key_prefix}_date"] = CNEDates.get_default_date()
    return col.date_input(label=label, min_value=all_dates[0], max_value=all_dates[-1], key=f"{key_prefix}_date")


def get_rental_selection(
        data_service: DataService,
        in_progress_rentals_only: bool,
        key_prefix: str,
) -> Tuple[date, Optional[str], Optional[dict]]:
    """Render rental retrival options and return the selected rental."""

    col1, col2 = st.columns([1, 2])
    rental_date = get_date_input(label="Rental Date", col=col1, key_prefix=key_prefix)
    rentals = data_service.get_rentals_on_date(
        rental_date=rental_date,
        in_progress_rentals_only=in_progress_rentals_only,
    )
    if rentals is None or rentals.empty:
        st.warning(f"**No Rentals Today**: There are no rentals on {rental_date.strftime('%b %d, %Y')}.")
        return rental_date, None, None

    rental_id = col2.selectbox(
        label="Select a Rental",
        options=sorted(rentals["device_id"] + " - " + rentals["name"] + " (Rental ID: " + rentals["id"] + ")"),
        index=None,
        key=f"{key_prefix}_rental_selection",
    )
    rental_id = rental_id.split("Rental ID: ")[1][:-1] if rental_id else None
    if not rental_id:
        return rental_date, None, None
    return rental_date, rental_id, rentals.loc[rentals["id"] == rental_id].to_dict(orient="records")[0]


def clear_session_state_for_form(clear_prefixes: List[str]):
    """Clear session state data with a given list of prefixes"""
    for key in st.session_state.keys():
        if any(key.startswith(prefix) for prefix in clear_prefixes):
            del st.session_state[key]
            if "items_left_behind" in key:
                continue
            if "button" not in key:
                st.session_state[key] = None


def initialize_form(
        form_prefix: str,
        set_default_date: Optional[bool] = False,
        set_default_time: Optional[bool] = False,
        default_date: Optional[date] = CNEDates.get_default_date(),
        default_time: Optional[time] = datetime.now(tz=get_default_timezone()).time(),
):
    """Initialize a form by setting date/time fields"""
    if set_default_date:
        if st.session_state.get(f"{form_prefix}_date") is None:
            st.session_state[f"{form_prefix}_date"] = default_date
    if set_default_time:
        if st.session_state.get(f"{form_prefix}_time") is None:
            st.session_state[f"{form_prefix}_time"] = default_time


def process_validation_errors(error_key: str):
    """Decorator to process validation errors and store them in session state"""

    def inner(func):
        """Inner decorator function"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function"""
            st.session_state[error_key] = None  # clear previous errors
            try:
                func(*args, **kwargs)
            except ValidationError as exc:
                st.session_state[error_key] = exc.errors()
                st.rerun()

        return wrapper

    return inner
