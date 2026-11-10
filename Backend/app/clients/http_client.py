from typing import Any
import httpx

class ExternalApiError(Exception):
    def __init__(self, provider: str, message: str, category: str = "unknown"):
        self.provider = provider
        self.message = message
        self.category = category
        super().__init__(message)

class HttpClient:
    def __init__(self, timeout_seconds: float = 10.0):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds)
        )

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        provider: str,
    ) -> dict[str, Any]:
        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise ExternalApiError(
                provider,
                "외부 API 요청 시간 초과",
                "timeout",
            ) from exc
        except httpx.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            category = (
                "authentication" if status_code in {401, 403}
                else "server" if status_code is not None and status_code >= 500
                else "http"
            )
            raise ExternalApiError(
                provider,
                "외부 API 요청 실패",
                category,
            ) from exc
        except ValueError as exc:
            raise ExternalApiError(
                provider,
                "외부 API 응답 형식이 올바르지 않음"
            ) from exc

    async def close(self) -> None:
        await self.client.aclose()
