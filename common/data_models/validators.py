def check_cne_year_and_date(model):
    """Validate that the CNE year and date match"""
    if model.cne_year != model.date.year:
        raise ValueError(f"CNE Year ({model.cne_year}) and date ({model.date}) do not match")
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
