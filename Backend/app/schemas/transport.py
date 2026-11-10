from enum import StrEnum

class TransportType(StrEnum):
    BUS = "BUS"
    SUBWAY = "SUBWAY"
    WALK = "WALK"
class ApiProvider(StrEnum):
    ODSAY = "ODSAY"
    SEOUL_OPEN_DATA = "SEOUL_OPEN_DATA"
    PUBLIC_DATA = "PUBLIC_DATA"