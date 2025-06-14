from datetime import datetime, timedelta
from typing import Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common.constants import ReservationStatus, DeviceType
from common.data_models.reservation import Reservation, NewReservation
from common.utils import get_default_timezone
from ui.forms.reservation_form import ReservationForm
from ui.src.constants import CNEDates, Colour
from ui.src.data_service import DataService
from ui.src.utils import process_validation_errors


# pylint: disable=trailing-whitespace
@st.dialog("Success!")
def display_success_dialog(reservation_id: str, reservation: Union[NewReservation, Reservation], is_update: bool):
    """Display the success dialog upon creating/updating a reservation"""
    st.success(
        f"""
        The following **{reservation.device_type}** reservation was 
        {'updated' if is_update else 'created'} successfully:

        * **Reservation ID**: {reservation_id}
        * **Name**: {reservation.name}
        * **Date**: {reservation.date.strftime('%b %d, %Y')}
        * **Time**: {reservation.reservation_time.strftime('%I:%M %p')}
        * **Location**: {reservation.location}
        * **Status**: {reservation.status}
        """
    )
    if st.button("Close"):
        st.rerun()


@process_validation_errors(error_key="new_reservation_form_errors")
def submit_new_reservation_form(reservation: dict, is_waitlisted: bool):
    """Submit the reservation form"""

    reservation["reservation_time"] = get_default_timezone().localize(
        datetime.combine(reservation["date"], reservation["reservation_time"])
    )
    reservation["cne_year"] = CNEDates.get_cne_year()
    if is_waitlisted:
        reservation["status"] = ReservationStatus.WAITLISTED
    else:
        reservation["status"] = ReservationStatus.get_default_reservation_status(device_type=reservation["device_type"])

    reservation = NewReservation(**reservation)
    status_code, result = DataService().add_new_reservation(reservation=reservation)
    if status_code == 200:
        display_success_dialog(reservation_id=result, reservation=reservation, is_update=False)
        ReservationForm(key_prefix="new_reservation").clear_form()


@process_validation_errors(error_key="update_reservation_form_errors")
def submit_update_reservation_form(reservation: dict):
    """Submit the reservation form"""

    reservation["reservation_time"] = get_default_timezone().localize(
        datetime.combine(reservation["date"], reservation["reservation_time"])
    )

    reservation = Reservation(**reservation)
    status_code = DataService().update_reservation(reservation=reservation)
    if status_code == 200:
        display_success_dialog(reservation_id=reservation.id, reservation=reservation, is_update=True)
        ReservationForm(key_prefix="update_reservation").clear_form()


def update_reservation_status(reservation: Reservation, status: ReservationStatus):
    """Update the reservation status"""
    reservation.status = status
    status_code = DataService().update_reservation_status(reservation_id=reservation.id, status=status)
    if status_code == 200:
        display_success_dialog(reservation_id=reservation.id, reservation=reservation, is_update=True)


def create_reservation_availability_chart(reservation_counts: pd.DataFrame, device_type: DeviceType, limit: int):
    """
    Create a heatmap chart showing reservation availability for a specific device type.
    Args:
        reservation_counts (pd.DataFrame): DataFrame containing reservation counts with
          columns 'date', 'device_type', and 'count'.
        device_type (str): The type of device for which to create the availability chart.
        limit (int): The maximum number of reservations allowed for the device type.
    """
    # get all dates for the calendar
    start_date, end_date = CNEDates.get_cne_start_end_dates()
    reservation_df = pd.DataFrame(
        data={
            "date": pd.date_range(
                start=start_date - timedelta(days=start_date.weekday() + 1 % 7),
                end=end_date + timedelta(days=(5 - end_date.weekday()) % 7),
                freq='D',
            )
        }
    )

    reservation_df = pd.merge(
        reservation_df,
        reservation_counts[reservation_counts["device_type"] == device_type].groupby(by="date")["count"].sum(),
        on="date",
        how="left",
    )
    reservation_df["label"] = np.where(
        reservation_df["date"].between(start_date, end_date),
        reservation_df["date"].dt.strftime("%b %d"),
        "",
    )
    reservation_df["availability"] = (1 - (reservation_df["count"] / limit)).clip(lower=0, upper=1)
    reservation_df["remaining"] = (limit - reservation_df["count"]).clip(lower=0)
    warning_level = max(0.2 * limit, 2.0) / limit  # Ensure at least 1 reservation is considered for warning

    # Fixed colour scale: 0 = red, (0, warning_level] = yellow, (warning_level, 1] = green
    colorscale = [
        [0.0, Colour.RESERVATIONS_NONE],
        [1e-6, Colour.RESERVATIONS_LOW if warning_level > 0 else Colour.RESERVATIONS_AVAILABLE],
        [warning_level, Colour.RESERVATIONS_LOW],
        [min(1.0, warning_level + 1e-6), Colour.RESERVATIONS_AVAILABLE],
        [1.0, Colour.RESERVATIONS_AVAILABLE]
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=reservation_df["availability"].values.reshape(-1, 7)[::-1],
            text=reservation_df["label"].values.reshape(-1, 7)[::-1],
            texttemplate="%{text}",
            textfont={"size": 14},
            customdata=np.dstack((
                reservation_df["date"].dt.strftime("%b %d, %Y").values.reshape(-1, 7)[::-1],
                reservation_df["count"].fillna(0).values.reshape(-1, 7)[::-1],
                reservation_df["remaining"].fillna(0).values.reshape(-1, 7)[::-1]
            )),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Reserved: %{customdata[1]}<br>"
                "Available: %{customdata[2]}<extra></extra>"
            ),
            colorscale=colorscale,
            zmin=0,
            zmax=1,
            showscale=False,
            xgap=5,
            ygap=5,
        )
    )
    fig.update_xaxes(
        showline=False,
        showgrid=False,
        zeroline=False,
        tickmode="array",
        tickvals=list(range(7)),
        ticktext=["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        tickfont={"size": 14}
    )
    fig.update_yaxes(showline=False, showgrid=False, zeroline=False, showticklabels=False, title=None)
    # Make cells square by setting aspect ratio and remove top margin
    fig.update_layout(
        autosize=True,
        height=350,
        margin={"t": 10, "b": 40, "l": 40, "r": 40},  # Reduce top margin
    )
    st.plotly_chart(fig)
