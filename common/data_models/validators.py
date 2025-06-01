import pycountry


def check_cne_year_and_date(model):
    """Validate that the CNE year and date match"""
    if model.cne_year != model.date.year:
        raise ValueError(f"CNE Year ({model.cne_year}) and date ({model.date}) do not match")
    return model


def check_country_code(country: str):
    """Parse country into 3-letter code"""
    try:
        # add support for common country names
        if country == "UK":
            country = "United Kingdom"
        return pycountry.countries.lookup(country).alpha_3
    except LookupError as exc:
        raise ValueError(f"Invalid country name: {country}") from exc


def check_province_state(model):
    """Validate that the province/state is provided for Canada or US"""

    # Only apply for Canada or US
    if model.country not in {"CAN", "USA"}:
        return model

    subdivisions = pycountry.subdivisions.get(country_code=pycountry.countries.lookup(model.country).alpha_2)
    if not subdivisions:
        raise ValueError(f"No subdivisions found for country code: {model.country}")

    province_input = model.province.strip().upper()
    code_map = {sub.code.split('-')[1].upper(): sub.code.split('-')[1] for sub in subdivisions}
    name_map = {sub.name.upper(): sub.code.split('-')[1] for sub in subdivisions}

    if province_input in code_map:
        model.province = code_map[province_input]
    elif province_input in name_map:
        model.province = name_map[province_input]
    else:
        raise ValueError(f"Invalid province/state '{model.province}' for {model.country}")

    return model


def check_device_id_and_type(model):
    """Validate that the device ID and type match"""
    if not model.device_id.startswith(model.device_type.get_prefix()):
        raise ValueError(f"Device ID ({model.device_id}) and type ({model.device_type}) do not match")
    return model


def check_reservation_id_and_type(model):
    """Validate that the reservation ID and type match"""
    if model.reservation_id:
        if not model.reservation_id.startswith(model.device_type.get_prefix()):
            raise ValueError(f"Reservation ID ({model.reservation_id}) and type ({model.device_type}) do not match")
    return model
