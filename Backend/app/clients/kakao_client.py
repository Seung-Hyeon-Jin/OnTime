import logging
from app.clients.http_client import HttpClient
from app.core.config import settings
from app.schemas.location import LocationSearchResponse, LocationSearchResultItem

logger = logging.getLogger(__name__)
class KakaoClient:
    KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
    ADDRESS_URL = "https://dapi.kakao.com/v2/local/search/address.json"

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    async def search_places(self, query: str) -> LocationSearchResponse:
        api_key = settings.KAKAO_REST_API_KEY

        # 카카오 API 키가 설정되어 있지 않거나 비어있는 경우
        if not api_key or api_key.strip() == "" or "YOUR_KAKAO" in api_key:
            return self._fallback_search(query)

        headers = {
            "Authorization": f"KakaoAK {api_key.strip()}",
        }
        params = {
            "query": query,
            "size": 15,
        }

        items = []

        # 1. 키워드/장소명 검색
        try:
            kw_data = await self.http_client.get_json(
                self.KEYWORD_URL,
                params=params,
                headers=headers,
                provider="kakao",
            )
            items.extend(self._parse_keyword_docs(kw_data))
        except Exception as e:
            logger.warning("키워드 검색 실패 (쿼리: %r): %s", query,e)


        # 2. 도로명/지번 주소 검색
        try:
            addr_data = await self.http_client.get_json(
                self.ADDRESS_URL,
                params=params,
                headers=headers,
                provider="kakao",
            )
            items.extend(self._parse_address_docs(addr_data))
        except Exception as e:
            logger.warning("주소 검색 실패 (쿼리: %r): %s", query, e)


        # 카카오 API에서 결과가 검색된 경우 중복 제거 후 반환
        if items:
            seen = set()
            unique_items = []
            for item in items:
                key = f"{item.place_name}_{item.latitude}_{item.longitude}"
                if key not in seen:
                    seen.add(key)
                    unique_items.append(item)
        if len(errors) == 2:
            raise errors[0]

        return LocationSearchResponse(query=query, items=unique_items)


    async def reverse_geocode(self, lat: float, lng: float) -> dict:
        api_key = settings.KAKAO_REST_API_KEY
        if not api_key or api_key.strip() == "" or "YOUR_KAKAO" in api_key:
            return {
                "address_name": "내위치",
                "latitude": lat,
                "longitude": lng,
            }

        headers = {"Authorization": f"KakaoAK {api_key.strip()}"}
        url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
        params = {"x": str(lng), "y": str(lat)}

        try:
            data = await self.http_client.get_json(
                url, params=params, headers=headers, provider="kakao"
            )
            docs = data.get("documents", [])
            if docs:
                doc = docs[0]
                road = doc.get("road_address") or {}
                addr = doc.get("address") or {}
                name = road.get("address_name") or addr.get("address_name") or "내 현재 위치"
                return {"address_name": name, "latitude": lat, "longitude": lng}
        except Exception:
            pass

        return {
            "address_name": f"내 위치 ({lat:.4f}, {lng:.4f})",
            "latitude": lat,
            "longitude": lng,
        }

    def _parse_keyword_docs(self, data: dict) -> list[LocationSearchResultItem]:
        documents = data.get("documents", [])
        items = []

        for doc in documents:
            try:
                place_name = doc.get("place_name", "")
                address_name = doc.get("address_name", "")
                road_address_name = doc.get("road_address_name") or address_name
                lng = float(doc.get("x", 0.0))
                lat = float(doc.get("y", 0.0))
                category = doc.get("category_group_name") or doc.get("category_name")

                if lat != 0.0 and lng != 0.0:
                    items.append(
                        LocationSearchResultItem(
                            place_name=place_name,
                            address_name=address_name,
                            road_address_name=road_address_name,
                            latitude=lat,
                            longitude=lng,
                            category_name=category,
                        )
                    )
            except (ValueError, TypeError):
                continue

        return items

    def _parse_address_docs(self, data: dict) -> list[LocationSearchResultItem]:
        documents = data.get("documents", [])
        items = []

        for doc in documents:
            try:
                address = doc.get("address") or {}
                road = doc.get("road_address") or {}
                place_name = road.get("address_name") or address.get("address_name") or "검색 주소"
                address_name = address.get("address_name") or place_name
                road_address_name = road.get("address_name") or address_name
                lng = float(doc.get("x", 0.0))
                lat = float(doc.get("y", 0.0))

                if lat != 0.0 and lng != 0.0:
                    items.append(
                        LocationSearchResultItem(
                            place_name=place_name,
                            address_name=address_name,
                            road_address_name=road_address_name,
                            latitude=lat,
                            longitude=lng,
                            category_name="주소",
                        )
                    )
            except (ValueError, TypeError):
                continue

        return items

    def _fallback_search(self, query: str) -> LocationSearchResponse:
        q = query.lower().strip()
        items = []

        if "천안" in q or "천안캠" in q:
            items.append(
                LocationSearchResultItem(
                    place_name="단국대학교 천안캠퍼스",
                    address_name="충남 천안시 동남구 단국대길 119",
                    road_address_name="충남 천안시 동남구 단국대길 119",
                    latitude=36.8335,
                    longitude=127.1670,
                    category_name="학교",
                )
            )

        if "죽전" in q or "죽전캠" in q or "죽전동" in q:
            items.append(
                LocationSearchResultItem(
                    place_name="단국대학교 죽전캠퍼스",
                    address_name="경기 용인시 수지구 죽전동 1261",
                    road_address_name="경기 용인시 수지구 죽전로 152",
                    latitude=37.3218,
                    longitude=127.1268,
                    category_name="학교",
                )
            )

        if "성채안로" in q or "봉담" in q or "오목천" in q:
            items.append(
                LocationSearchResultItem(
                    place_name="성채안로 26",
                    address_name="경기 수원시 권선구 오목천동 1148",
                    road_address_name="경기 수원시 권선구 성채안로 26",
                    latitude=37.2582,
                    longitude=126.9634,
                    category_name="주소",
                )
            )

        if "광주" in q or "챔피언스" in q:
            items.append(
                LocationSearchResultItem(
                    place_name="광주기아챔피언스필드",
                    address_name="광주 북구 임동 102",
                    road_address_name="광주 북구 서림로 10",
                    latitude=35.1681,
                    longitude=126.8891,
                    category_name="경기장",
                )
            )

        if not items:
            items.append(
                LocationSearchResultItem(
                    place_name=f"{query} 검색 위치",
                    address_name=f"{query} (검색 주소)",
                    road_address_name=query,
                    latitude=37.5665,
                    longitude=126.9780,
                    category_name="검색위치",
                )
            )

        return LocationSearchResponse(query=query, items=items)
