from enum import StrEnum

DEVICE_ID_PATTERN = r"[S|W][0-9]{2}"
RENTAL_ID_PATTERN = r"[S|W]0[8-9][0-9]{2}[0-9]{3}"
RESERVATION_ID_PATTERN = r"[S|W]0[8-9][0-9]{2}[0-9]{3}"
WALK_IN_RESERVATION_ID = "Walk-In (No Reservation)"


class DeviceStatus(StrEnum):
    """Status of a mobility device"""
    AVAILABLE = "Available"
    BACKUP = "Backup"
    OUT_OF_SERVICE = "Out of Service"
    RENTED = "Rented"

    @classmethod
    def get_device_status_colour(cls, status):
        """Get the colour for a device status"""
        match status:
            case cls.AVAILABLE:
                return "#49994C"
            case cls.BACKUP:
                return "#A6A6A6"
            case cls.OUT_OF_SERVICE:
                return "#D94936"
            case cls.RENTED:
                return "#E6920B"
            case _:
                raise ValueError(f"Unrecognized device status {status}")


class DeviceType(StrEnum):
    """Types of mobility device available for rent"""
    __SCOOTER_DEPOSIT = 100
    __SCOOTER_FEE = 45
    __WHEELCHAIR_DEPOSIT = 50
    __WHEELCHAIR_FEE = 20

    SCOOTER = "Scooter"
    WHEELCHAIR = "Wheelchair"

    @classmethod
    def get_fee_amount(cls, device):
        """Get the rental fee for a given device type"""
        match device:
            case cls.SCOOTER:
                return DeviceType.__SCOOTER_FEE
            case cls.WHEELCHAIR:
                return DeviceType.__WHEELCHAIR_FEE
            case _:
                raise ValueError(f"Unrecognized device {device}")

    @classmethod
    def get_deposit_amount(cls, device):
        """Get the deposit amount for a given device type"""
        match device:
            case cls.SCOOTER:
                return DeviceType.__SCOOTER_DEPOSIT
            case cls.WHEELCHAIR:
                return DeviceType.__WHEELCHAIR_DEPOSIT
            case _:
                raise ValueError(f"Unrecognized device {device}")

    def get_device_prefix(self):
        """Get the prefix for a device (for IDs)"""
        return self.value[0]


class HoldItem(StrEnum):
    """Items that may be left behind by a renter"""
    CANE = 'Cane'
    CRUTCHES = 'Crutches'
    STROLLER = 'Stroller'
    WALKER = 'Walker'
    WHEELCHAIR = 'Wheelchair'
    OTHER = 'Other'


class Location(StrEnum):
    """Rental locations"""
    BLC = "BLC"
    PG = "PG"


class PaymentMethod(StrEnum):
    """Possible payment methods"""
    CASH = "Cash"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"

    @classmethod
    def get_accepted_deposit_payment_methods(cls):
        """Get a set of accepted deposit payment methods"""
        return {cls.CASH, cls.CREDIT_CARD}

    @classmethod
    def get_accepted_fee_payment_methods(cls):
        """Get a set of accepted fee payment methods"""
        return {cls.CASH, cls.CREDIT_CARD, cls.DEBIT_CARD}


class ReservationStatus(StrEnum):
    """Reservation statuses"""
    PENDING = "Pending Confirmation"
    CONFIRMED = "Confirmed"
    RESERVED = "Reserved"
    PICKED_UP = "Picked Up"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

    @classmethod
    def get_default_reservation_status(cls, device_type: DeviceType):
        """Get the default reservation status for a given device type"""
        match device_type:
            case DeviceType.SCOOTER:
                return cls.PENDING
            case DeviceType.WHEELCHAIR:
                return cls.RESERVED
            case _:
                raise ValueError(f"Unrecognized device type {device_type}")
