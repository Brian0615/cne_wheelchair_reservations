import io
from datetime import date, datetime

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from common.constants import DeviceType, WALK_IN_RESERVATION_ID, RentalStatus
from common.data_models import CompletedRental, NewRental, ChangeDeviceInfo
from common.utils import get_default_timezone
from ui.forms import NewRentalForm
from ui.pdf_forms.scooter_pdf_form import ScooterPDFForm
from ui.pdf_forms.wheelchair_pdf_form import WheelchairPDFForm
from common.cne_dates import CNEDates
from ui.src.constants import Colour
from ui.src.data_service import DataService
from ui.src.reservation_utils import load_fonts
from ui.src.utils import clear_session_state_for_form, process_validation_errors


def on_dismiss_complete_rental_success_dialog():
    """Callback for when the success dialog is dismissed"""
    clear_session_state_for_form(clear_prefixes=["complete_rental_"])


@st.dialog("Success!", on_dismiss=on_dismiss_complete_rental_success_dialog)
def display_complete_rental_success_dialog(completed_rental: CompletedRental):
    """Display the success dialog upon completing a rental"""

    st.success(
        f"""
        The following rental was completed successfully:

        * **Rental ID**: {completed_rental.id}
        * **Name**: {completed_rental.name}
        * **Returned Chair/Scooter**: {completed_rental.device_id}
        """
    )


def on_dismiss_new_rental_success_dialog():
    """Callback for when the success dialog is dismissed"""
    clear_session_state_for_form(clear_prefixes=["new_rental_"])
    NewRentalForm(key_prefix="new_rental").clear_form()


@st.dialog("Success!", on_dismiss=on_dismiss_new_rental_success_dialog)
def display_new_rental_success_dialog(rental_id: str, new_rental: NewRental, form_data: bytes):
    """Display the success dialog upon creating a new rental"""
    st.success(
        f"""
        The following rental was created successfully:
        
        * **Name**: {new_rental.name}
        * **{new_rental.device_type}**: {new_rental.device_id}
        * **Rental ID**: {rental_id}
        """
    )
    st.download_button(
        label="Download Rental Form",
        data=form_data,
        icon=":material/download:",
        file_name=f"rental_form_{rental_id}.pdf",
    )


def get_pdf_form_class(device_type: DeviceType):
    """Get the PDF form class based on the device type"""
    if device_type == DeviceType.WHEELCHAIR:
        return WheelchairPDFForm
    if device_type == DeviceType.SCOOTER:
        return ScooterPDFForm
    raise ValueError(f"Unsupported device type: {device_type}")


@process_validation_errors(error_key="complete_rental_errors")
def submit_complete_rental_form(completed_rental: dict):
    """Complete a rental"""

    completed_rental["cne_year"] = CNEDates.get_cne_year()

    # update return time
    completed_rental["return_time"] = get_default_timezone().localize(
        datetime.combine(completed_rental["return_date"], completed_rental["return_time"])
    )
    completed_rental.pop("return_date")

    # validate rental completion data
    completed_rental = CompletedRental(**completed_rental)

    # complete rental
    data_service = DataService()
    status_code, result = data_service.complete_rental(completed_rental)
    if status_code == 200:
        display_complete_rental_success_dialog(completed_rental)
    else:
        st.error(
            f"""
            **API Error**
            * Error Code: {status_code}
            * Error Message: {result}
            """
        )


@process_validation_errors(error_key="rental_form_errors")
def submit_new_rental_form(new_rental: dict):
    """Submit the new rental form"""

    new_rental["cne_year"] = CNEDates.get_cne_year()
    new_rental["pickup_time"] = get_default_timezone().localize(
        datetime.combine(new_rental["date"], new_rental["pickup_time"])
    )
    new_rental["status"] = RentalStatus.IN_PROGRESS

    # don't put reservation ID if walk-in
    if new_rental["reservation_id"] == WALK_IN_RESERVATION_ID:
        new_rental["reservation_id"] = None

    # validate rental data
    new_rental = NewRental(**new_rental)

    # try to add the new rental
    data_service = DataService()
    status_code, add_result = data_service.add_new_rental(new_rental)
    if status_code == 200:
        form_data = get_pdf_form_class(device_type=new_rental.device_type)(
            rental_data=new_rental,
            rental_id=add_result,
        ).export_form_to_bytes()
        status_code, upload_result = data_service.upload_rental_form(pdf_bytes=form_data, rental_id=add_result)

        if status_code == 200:
            display_new_rental_success_dialog(rental_id=add_result, new_rental=new_rental, form_data=form_data)
        else:
            st.error(
                f"""
                **API Error**
                * Error Code: {status_code}
                * Error Message: {upload_result}
                """
            )
    else:
        st.error(
            f"""
            **API Error**
            * Error Code: {status_code}
            * Error Message: {add_result}
            """
        )


def on_dismiss_change_device_success_dialog():
    """Callback for when the success dialog is dismissed"""
    clear_session_state_for_form(clear_prefixes=["manage_rental_", "change_device_"])


@st.dialog("Success!", on_dismiss=on_dismiss_change_device_success_dialog)
def display_change_device_success_dialog(change_data: ChangeDeviceInfo):
    """Display the success dialog upon changing a device"""
    st.success(
        f"""
        The following rental was updated successfully:

        * **Rental ID**: {change_data.id}
        * **Old Device ID**: {change_data.old_device_id}
        * **New Device ID**: {change_data.new_device_id}
        """
    )


@process_validation_errors(error_key="change_device_errors")
def change_rental_device(change_data: dict):
    """Change a device on a current rental"""

    # validate change device data
    change_data = ChangeDeviceInfo(**change_data)

    # change device
    status_code, _ = DataService().change_rental_device(change_data)
    if status_code == 200:
        display_change_device_success_dialog(change_data)


def export_late_returns_to_pdf(rentals_df: pd.DataFrame, rental_date: date) -> bytes:
    """
    Export a day's late (not yet returned) rentals to a PDF file, with a signature column
    for the guest to acknowledge deposit pickup and sign-off lines for CNE staff.

    Args:
        rentals_df: DataFrame containing rental data
        rental_date: The date for which late returns are being exported (for title only)

    Returns:
        PDF file as bytes that can be used for download
    """
    regular_font, bold_font = load_fonts()

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(letter),
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    elements = [
        Paragraph(
            text=f"Late Returns - {rental_date.strftime('%B %d, %Y')}",
            style=ParagraphStyle(
                name='CustomHeading1',
                parent=getSampleStyleSheet()['Heading1'],
                fontName=bold_font,
            )
        ),
        Spacer(1, 0.25 * inch),
    ]

    late_returns = rentals_df[rentals_df["return_time"].isna()].copy()
    if late_returns.empty:
        elements.append(Paragraph(text="There are no late returns.", style=getSampleStyleSheet()["Normal"]))
    else:
        late_returns["phone_number"] = late_returns["phone_number"].astype(str).str.replace(
            r"^tel:", "", regex=True
        )
        late_returns["items_left_behind"] = late_returns["items_left_behind"].apply(
            lambda items: ", ".join(items) if items else ""
        )
        late_returns["deposit_payment_amount"] = late_returns["deposit_payment_amount"].apply(
            lambda amount: f"${amount:.0f}"
        )
        late_returns["signature"] = ""

        # wrap long text so it doesn't overflow its column
        late_returns["name"] = late_returns["name"].str.wrap(20, break_long_words=False)
        late_returns["items_left_behind"] = late_returns["items_left_behind"].str.wrap(15, break_long_words=False)
        late_returns = late_returns.rename(columns={
            "id": "rental_id",
            "name": "renter_name",
            "phone_number": "renter_phone_number",
            "pickup_location": "location",
            "deposit_payment_method": "deposit_method",
            "deposit_payment_amount": "deposit_amount",
            "items_left_behind": "notes",
        })
        columns = [
            "rental_id", "renter_name", "renter_phone_number", "device_id", "location",
            "deposit_method", "deposit_amount", "notes", "signature",
        ]
        column_headers = {
            "rental_id": "Rental ID",
            "renter_name": "Name",
            "renter_phone_number": "Phone Number",
            "location": "Location",
            "deposit_method": "Deposit",
            "deposit_amount": "Amount",
            "notes": "Notes",
            "signature": "Signature",
        }

        for device_type in DeviceType:
            device_late_returns = late_returns[late_returns["device_type"] == device_type][columns]
            if device_late_returns.empty:
                continue
            device_late_returns = device_late_returns.sort_values(by="rental_id")

            elements.append(
                Paragraph(
                    text=f"{device_type} Late Returns",
                    style=ParagraphStyle(name='CustomHeading2', parent=getSampleStyleSheet()['Heading2'],
                                          fontName=bold_font)
                )
            )
            elements.append(Spacer(1, 0.1 * inch))

            # Prepare table data; the device ID column is labelled with the device type itself
            headers = [str(device_type) if col == "device_id" else column_headers[col] for col in columns]
            table_data = [headers]
            for _, row in device_late_returns.iterrows():
                table_data.append(['' if pd.isna(item) else str(item) for item in row.tolist()])

            # Create table
            table = Table(
                table_data,
                repeatRows=1,
                colWidths=[x * inch for x in (0.8, 1.75, 1.5, 0.75, 0.75, 0.75, 0.75, 1.25, 0.75)],
            )

            # Apply table styles
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), Colour.TABLE_HEADER),  # Header background
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Header text color
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center all cells
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Left-align Name column
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

            # Add alternating row colors
            for i in range(1, len(table_data)):
                if i % 2 == 0:
                    table_style.add('BACKGROUND', (0, i), (-1, i), Colour.TABLE_ALTERNATE_LIGHT_GREY)

            table.setStyle(table_style)
            elements.append(table)
            elements.append(Spacer(1, 0.3 * inch))

    # Signature lines for handing off the late returns and deposits to CNE late returns staff
    elements.append(Spacer(1, 0.75 * inch))
    signature_style = ParagraphStyle(
        name='Signature',
        parent=getSampleStyleSheet()['Normal'],
        fontName=regular_font,
        fontSize=11,
    )
    signature_table = Table(
        [[
            Paragraph("Issued by: " + "_" * 45, signature_style),
            Paragraph("Received by: " + "_" * 45, signature_style),
        ]],
        colWidths=[5 * inch, 5 * inch],
    )
    elements.append(signature_table)

    # Build PDF document
    doc.build(elements)

    # Return the PDF file as bytes
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
