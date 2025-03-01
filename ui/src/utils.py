import math
from datetime import date, datetime, time
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st
from plotly import graph_objects as go
from pydantic import BaseModel

from common.constants import DeviceStatus
from common.utils import get_default_timezone
from ui.src.constants import CNEDates
from ui.src.data_service import DataService


# noinspection PyTypeChecker
def create_inventory_chart(inventory: pd.DataFrame):
    """Create a chart to display the inventory."""

    fig = go.Figure()
    num_per_row = 25
    num_rows = math.ceil(len(inventory) / num_per_row)
    fig.update_layout(
        autosize=False,
        width=num_per_row * 50,
        height=35 * num_rows,
        margin={"l": 0, "r": 0, "b": 0, "t": 0, "pad": 0},
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    fig.update_xaxes(range=[0, num_per_row], visible=False, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-2 * num_rows, 0], visible=False, showgrid=False, zeroline=False)
    for i, (_, device) in enumerate(inventory.iterrows()):
        x0, y0, x1, y1 = (
            i % num_per_row,
            -2 * (i // num_per_row),
            (i % num_per_row) + 0.8,
            -2 * (i // num_per_row) - 1.5
        )
        fig.add_trace(
            go.Scatter(
                x=[x0, x0, x1, x1, x0],
                y=[y0, y1, y1, y0, y0],
                fill="toself",
                fillcolor=DeviceStatus.get_device_status_colour(device["status"]),
                line_color=DeviceStatus.get_device_status_colour(device["status"]),
                mode="lines",
                text=f"<b>{device['id']}</b><br>Status: {device['status']}<br>Location: {device['location']}",
                hoverinfo="text",
                hoverlabel={"font_size": 14},
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[(x0 + x1) / 2.0],
                y=[(y0 + y1) / 2.0],
                mode="text",
                text=device["id"],
                textfont={"color": "#EEEEEE", "size": 14},
                textposition="middle center",
                showlegend=False,
                hoverinfo="skip",
            )
        )
    return fig


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
    return col.date_input(
        label=label,
        value=CNEDates.get_default_date(),
        min_value=all_dates[0],
        max_value=all_dates[-1],
        key=f"{key_prefix}_date",
    )


def get_rental_selection(
        data_service: DataService,
        in_progress_rentals_only: bool,
        key_prefix: str,
) -> Tuple[date, Optional[str], Optional[dict]]:
    """Render rental retrival options and return the selected rental."""

    # noinspection PyShadowingNames
    @st.cache_data(ttl=30, show_spinner=False)
    def get_rentals_on_date_helper(rental_date: date, in_progress_rentals_only: bool):
        """Helper function to get rentals, for caching purposes"""
        return data_service.get_rentals_on_date(
            rental_date=rental_date,
            in_progress_rentals_only=in_progress_rentals_only,
        )

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
