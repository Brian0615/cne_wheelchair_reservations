import os

from pypdf import PdfReader, PdfWriter

from common.data_models.rental import NewRental


class WheelchairForm:
    __DEFAULT_FORM_PATH = "completed_forms"

    def __init__(self):
        self.reader = PdfReader(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "assets/wheelchair_form_fillable.pdf"
            )
        )
        self.writer = PdfWriter()

    def fill_form(self, rental_data: NewRental, rental_id: str):
        """Create a PDF wheelchair form with the rental data"""
        self.writer.append(self.reader)
        self.writer.update_page_form_field_values(
            self.writer.pages[0],
            {
                "rental_id": rental_id,
                "wheelchair_id": rental_data.device_id,
                "date": rental_data.date.strftime("%b %d, %Y"),
                "name": rental_data.name,
                "phone_number": rental_data.phone_number,
                "address": rental_data.address,
                "city": rental_data.city,
                "province_state": rental_data.province,
                "postal_code": rental_data.postal_code,
                "country": rental_data.country,
                "fee_payment_method": rental_data.fee_payment_method.lower().replace(" ", "_"),
                "deposit_payment_method": rental_data.deposit_payment_method.lower().replace(" ", "_"),
                "id_verified": "yes",
                "time_out": rental_data.pickup_time.strftime("%I:%M %p"),
                "staff_name": rental_data.staff_name,
                "rental_id_receipt": rental_id,
                "wheelchair_id_receipt": rental_data.device_id,
                "date_receipt": rental_data.date.strftime("%b %d, %Y"),
                "name_receipt": rental_data.name,
            },
            auto_regenerate=False
        )

        form_path = os.path.join(WheelchairForm.__DEFAULT_FORM_PATH, f"rental_form_{rental_id}.pdf")
        os.makedirs(os.path.dirname(form_path), exist_ok=True)
        with open(form_path, "wb") as stream:
            self.writer.write(stream)
        return form_path
