from ui.forms.form_fields import CheckboxField
from ui.forms.reservation_form import ReservationForm


class NewReservationForm(ReservationForm):
    """Reservation form extended with a waitlist-override checkbox for new reservations."""

    def __init__(self, key_prefix: str):
        super().__init__(key_prefix=key_prefix)
        self.fields["force_waitlist"] = CheckboxField(
            key=f"{key_prefix}_force_waitlist",
            label="Add to Waitlist (Override)",
        )

    def _render_extra_fields(self, result: dict, disabled: bool = False):
        result["force_waitlist"] = self.fields["force_waitlist"].render_field(disabled=disabled)
