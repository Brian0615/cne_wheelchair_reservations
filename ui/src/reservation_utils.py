import io
import itertools
import os
from datetime import datetime, timedelta
from typing import Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

from common.constants import ReservationStatus, DeviceType, Location
from common.data_models.reservation import Reservation, NewReservation
from common.utils import get_default_timezone
from common.cne_dates import CNEDates
from ui.forms.new_reservation_form import NewReservationForm
from ui.forms.reservation_form import ReservationForm
from ui.src.constants import Colour
from ui.src.data_service import DataService
from ui.src.display_utils import coerce_pandas_aware_datetime
from ui.src.utils import process_validation_errors


def on_dismiss_success_dialog():
    """Callback for when the success dialog is dismissed"""
    NewReservationForm(key_prefix="new_reservation").clear_form()
    ReservationForm(key_prefix="update_reservation").clear_form()


@st.dialog("Success!", on_dismiss=on_dismiss_success_dialog)
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


@process_validation_errors(error_key="new_reservation_form_errors")
def submit_new_reservation_form(reservation: dict, is_waitlisted: bool):
    """Submit the reservation form"""

    reservation["reservation_time"] = get_default_timezone().localize(
        datetime.combine(reservation["date"], reservation["reservation_time"])
    )
    reservation["cne_year"] = CNEDates.get_cne_year()
    if reservation["device_type"]:
        if is_waitlisted:
            reservation["status"] = ReservationStatus.WAITLISTED
        else:
            reservation["status"] = ReservationStatus.get_default_reservation_status(reservation["device_type"])

    reservation = NewReservation(**reservation)
    status_code, result = DataService().add_new_reservation(reservation=reservation)
    if status_code == 200:
        display_success_dialog(reservation_id=result, reservation=reservation, is_update=False)


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


def update_reservation_status(reservation: Reservation, status: ReservationStatus):
    """Update the reservation status."""
    reservation.status = status
    status_code = DataService().update_reservation_status(reservation_id=reservation.id, status=status)
    if status_code == 200:
        display_success_dialog(reservation_id=reservation.id, reservation=reservation, is_update=True)


def get_reservation_counts() -> pd.DataFrame:
    """
    Get the reservation counts for each date, device type, and location.
    """
    data_service = DataService()
    reservation_counts = data_service.get_reservation_count()
    default_table = pd.DataFrame(
        list(itertools.product(CNEDates.get_cne_date_list(), [x.value for x in DeviceType],
                               [x.value for x in Location])),
        columns=["date", "device_type", "location"],
    )
    default_table["date"] = pd.to_datetime(default_table["date"])
    if reservation_counts.empty:
        default_table["count"] = 0
        return default_table
    reservation_counts = default_table.merge(reservation_counts, on=["date", "device_type", "location"], how="left")
    reservation_counts = reservation_counts.fillna(0).sort_values(by=["date", "device_type", "location"])
    return reservation_counts


def create_reservation_availability_chart(
        reservation_counts: pd.DataFrame,
        device_type: DeviceType,
        limit: int,
        plot_height: int = 300,
):
    """
    Create a heatmap chart showing reservation availability for a specific device type.
    """
    start_date, end_date = CNEDates.get_cne_start_end_dates()
    reservation_df = pd.DataFrame(
        data={
            "date": pd.date_range(
                start=start_date - timedelta(days=(start_date.weekday() + 1) % 7),
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
    reservation_df["availability"] = (
        (1 - (reservation_df["count"] / limit)).clip(lower=0, upper=1) if limit > 0 else 0.0
    )
    reservation_df["remaining"] = (limit - reservation_df["count"]).clip(lower=0)
    warning_level = max(0.2 * limit, 2.0) / limit if limit > 0 else 1.0
    colorscale = [
        [0.0, Colour.RESERVATIONS_NONE],
        [1e-6, Colour.RESERVATIONS_LOW if warning_level > 0 else Colour.RESERVATIONS_AVAILABLE],
        [warning_level, Colour.RESERVATIONS_LOW],
        [min(1.0, warning_level + 1e-6), Colour.RESERVATIONS_AVAILABLE],
        [1.0, Colour.RESERVATIONS_AVAILABLE]
    ]
    fig = go.Figure(
        data=go.Heatmap(
            z=reservation_df["availability"].to_numpy().reshape(-1, 7)[::-1],
            text=reservation_df["label"].to_numpy().reshape(-1, 7)[::-1],
            texttemplate="%{text}",
            textfont={"size": 14},
            customdata=np.dstack((
                reservation_df["date"].dt.strftime("%b %d, %Y").to_numpy().reshape(-1, 7)[::-1],
                reservation_df["count"].fillna(0).to_numpy().reshape(-1, 7)[::-1],
                reservation_df["remaining"].fillna(0).to_numpy().reshape(-1, 7)[::-1]
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
    margin_factor = max(0.2, plot_height / 300.0)
    fig.update_layout(
        autosize=True,
        height=plot_height,
        margin={"t": 10, "b": 40 * margin_factor, "l": 40 * margin_factor, "r": 40 * margin_factor},
    )
    # remove the toolbar

    st.plotly_chart(fig, key=f"availability_chart_{device_type.value.lower()}", config={'displayModeBar': False})


def load_fonts():
    """
    Load custom fonts for the application.
    This function is called to ensure that the fonts are available for use in PDF generation.
    """
    # Register Roboto fonts
    roboto_font_path = os.path.join(os.getcwd(), "ui", "assets", "Roboto", "static")

    # Register Roboto Regular and Bold
    roboto_regular = os.path.join(roboto_font_path, "Roboto-Light.ttf")
    roboto_bold = os.path.join(roboto_font_path, "Roboto-Medium.ttf")

    if os.path.exists(roboto_regular) and os.path.exists(roboto_bold):
        pdfmetrics.registerFont(TTFont('Roboto', roboto_regular))
        pdfmetrics.registerFont(TTFont('Roboto-Bold', roboto_bold))

        # Define font names to use
        regular_font = 'Roboto'
        bold_font = 'Roboto-Bold'
    else:
        # Fallback to Helvetica if Roboto is not found
        regular_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'

    return regular_font, bold_font


def build_styled_table(
        table_data: list,
        col_widths: list,
        regular_font: str,
        bold_font: str,
        left_align_columns: tuple = (1,),
) -> Table:
    """
    Build a Table flowable with the header/stripe styling shared by the PDF exports in this app:
    a bold header row, centered cells (except the given left-aligned columns), and alternating
    row backgrounds.
    """
    table = Table(table_data, repeatRows=1, colWidths=col_widths)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), Colour.TABLE_HEADER),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center all cells
        ('FONTNAME', (0, 0), (-1, 0), bold_font),  # Bold for header
        ('FONTSIZE', (0, 0), (-1, 0), 11),  # Header font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Header padding
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Data rows background
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),  # Data rows text color
        ('FONTNAME', (0, 1), (-1, -1), regular_font),  # Data rows font
        ('FONTSIZE', (0, 1), (-1, -1), 10),  # Data rows font size
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertically center all text
        ('WORDWRAP', (0, 0), (-1, -1), True),  # Enable text wrapping for all cells
    ])
    for col in left_align_columns:
        table_style.add('ALIGN', (col, 0), (col, -1), 'LEFT')

    # Add alternating row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), Colour.TABLE_ALTERNATE_LIGHT_GREY)

    table.setStyle(table_style)
    return table


def export_reservations_to_pdf(reservations_df: pd.DataFrame, date: datetime.date) -> bytes:
    """
    Export reservations to a PDF file with one page per device type.

    Args:
        reservations_df: DataFrame containing reservation data
        date: The date for which reservations are being exported (for title only)

    Returns:
        PDF file as bytes that can be used for download
    """

    regular_font, bold_font = load_fonts()

    # Use BytesIO to create in-memory PDF file
    pdf_buffer = io.BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(letter),
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch
    )

    elements = []
    reservations_df["reservation_time"] = coerce_pandas_aware_datetime(reservations_df["reservation_time"])
    reservations_df["reservation_time"] = reservations_df["reservation_time"].dt.strftime("%I:%M %p")
    reservations_df["phone_number"] = reservations_df["phone_number"].str.lstrip("tel:")
    for _, device_type in enumerate(reservations_df['device_type'].unique()):
        # pandas 3.0 stores the column as plain strings; restore the enum for .value / label access
        device_type = DeviceType(device_type)
        # Filter the reservations for this device type
        device_reservations = reservations_df[reservations_df['device_type'] == device_type][
            ["id", "name", "phone_number", "reservation_time", "location", "status", "notes"]
        ]
        device_reservations = device_reservations.rename(columns={"reservation_time": "time"})
        device_reservations[DeviceType.get_short_label(device_type)] = None

        # wrap text
        device_reservations["name"] = device_reservations["name"].str.wrap(20, break_long_words=False)
        device_reservations["notes"] = device_reservations["notes"].str.wrap(20, break_long_words=False)

        # Add device type title to document
        elements.append(
            Paragraph(
                text=f"{device_type.value.capitalize()} Reservations - {date.strftime('%B %d, %Y')}",
                style=ParagraphStyle(
                    name='CustomHeading1',
                    parent=getSampleStyleSheet()['Heading1'],
                    fontName=bold_font,
                )
            )
        )
        elements.append(Spacer(1, 0.25 * inch))

        # Prepare table data
        table_data = [[col.replace('_', ' ').title().replace("Id", "ID") for col in device_reservations.columns]]
        for _, row in device_reservations.iterrows():
            # Leave cells empty for missing values instead of showing "None"/"nan" (pandas can upcast a
            # None from an object-dtype column to NaN when mixed with the other string-dtype columns here)
            table_data.append(['' if pd.isna(item) else str(item) for item in row.tolist()])

        # Create table
        table = build_styled_table(
            table_data,
            col_widths=[x * inch for x in (0.8, 1.75, 1.5, 0.95, 0.95, 1.75, 1.75, 0.8)],
            regular_font=regular_font,
            bold_font=bold_font,
            left_align_columns=(1, 6),  # Name, Notes
        )
        elements.append(table)
        elements.append(PageBreak())

    # Remove the last PageBreak to avoid an empty page
    elements = elements[:-1] if elements else []

    # Build PDF document
    doc.build(elements)

    # Return the PDF file as bytes
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
