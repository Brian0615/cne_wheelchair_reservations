import os
from io import BytesIO

import pymupdf

from common.data_models.rental import NewRental
from ui.src.utils import decode_signature_base64


class WheelchairForm:
    __DEFAULT_FORM_FOLDER = "completed_forms"
    __FILLABLE_FORM_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets/wheelchair_form_fillable.pdf"
    )

    @staticmethod
    def fill_form(rental_data: NewRental, rental_id: str):
        """Create a PDF wheelchair form with the rental data"""
        field_values = {
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
        }

        with pymupdf.open(WheelchairForm.__FILLABLE_FORM_PATH) as pdf:
            page = pdf[0]

            # fill in the form fields
            for widget in page.widgets():
                try:
                    widget.field_value = field_values[widget.field_name]
                    widget.update()
                except KeyError:
                    pass

            # insert the signature
            signature = decode_signature_base64(rental_data.signature)
            width, height = signature.size
            signature_io = BytesIO()
            signature.save(signature_io, format="png")
            signature_top_rect = pymupdf.Rect(78, 360, 78 + width * 29 / height, 389)
            signature_bottom_rect = pymupdf.Rect(78, 690, 78 + width * 29 / height, 719)
            page.insert_image(signature_top_rect, stream=signature_io)
            page.insert_image(signature_bottom_rect, stream=signature_io)

            form_path = os.path.join(WheelchairForm.__DEFAULT_FORM_FOLDER, f"rental_form_{rental_id}.pdf")
            os.makedirs(os.path.dirname(form_path), exist_ok=True)
            pdf.save(form_path)

        return form_path
