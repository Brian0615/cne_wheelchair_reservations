from typing import TypeVar

from ui.forms.form_fields.base_form_field import BaseFormField
from ui.forms.form_fields.button_field import ButtonField
from ui.forms.form_fields.checkbox_field import CheckboxField
from ui.forms.form_fields.date_field import DateField
from ui.forms.form_fields.multiselect_field import MultiSelectField
from ui.forms.form_fields.selectbox_field import SelectboxField
from ui.forms.form_fields.signature_field import SignatureField
from ui.forms.form_fields.text_field import TextField
from ui.forms.form_fields.time_field import TimeField

FormField = TypeVar("FormField", bound=BaseFormField)
