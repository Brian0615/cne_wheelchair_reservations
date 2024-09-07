from enum import StrEnum


class DeviceType(StrEnum):
    __SCOOTER_DEPOSIT = 100
    __SCOOTER_FEE = 45
    __WHEELCHAIR_DEPOSIT = 50
    __WHEELCHAIR_FEE = 20

    SCOOTER = "Scooter"
    WHEELCHAIR = "Wheelchair"

    @classmethod
    def get_fee_amount(cls, device):
        match device:
            case cls.SCOOTER:
                return DeviceType.__SCOOTER_FEE
            case cls.WHEELCHAIR:
                return DeviceType.__WHEELCHAIR_FEE
            case _:
                raise Exception(f"Unrecognized device {device}")

    @classmethod
    def get_deposit_amount(cls, device):
        match device:
            case cls.SCOOTER:
                return DeviceType.__SCOOTER_DEPOSIT
            case cls.WHEELCHAIR:
                return DeviceType.__WHEELCHAIR_DEPOSIT
            case _:
                raise ValueError(f"Unrecognized device {device}")


class Location(StrEnum):
    BLC = "BLC"
    PG = "PG"


class PaymentMethod(StrEnum):
    CASH = "Cash"
    CREDIT_CARD = "Credit Card"


class DeviceStatus(StrEnum):
    AVAILABLE = "Available"
    BACKUP = "Backup"
    OUT_OF_SERVICE = "Out of Service"
    RENTED = "Rented"

    @classmethod
    def status_to_int(cls, status) -> int:
        match status:
            case cls.AVAILABLE:
                return 1
            case cls.BACKUP:
                return 2
            case cls.OUT_OF_SERVICE:
                return 3
            case cls.RENTED:
                return 4
            case _:
                raise ValueError(f"Unrecognized status {status}")
