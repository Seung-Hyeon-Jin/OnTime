from pydantic import BaseModel


class LocationSearchResultItem(BaseModel):
    place_name: str
    address_name: str
    road_address_name: str | None = None
    latitude: float
    longitude: float
    category_name: str | None = None


class LocationSearchResponse(BaseModel):
    query: str
    items: list[LocationSearchResultItem]
