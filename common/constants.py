from enum import StrEnum


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


class Location(StrEnum):
    """Rental locations"""
    BLC = "BLC"
    PG = "PG"


class PaymentMethod(StrEnum):
    """Accepted payment methods"""
    CASH = "Cash"
    CREDIT_CARD = "Credit Card"


class DeviceStatus(StrEnum):
    """Status of a mobility device"""
    AVAILABLE = "Available"
    BACKUP = "Backup"
    OUT_OF_SERVICE = "Out of Service"
    RENTED = "Rented"
