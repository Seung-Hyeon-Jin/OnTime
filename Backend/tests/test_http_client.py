import unittest

import httpx

from app.clients.http_client import ExternalApiError, HttpClient


class HttpClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_becomes_external_api_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timed out", request=request)

        client = HttpClient()
        await client.client.aclose()
        client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            with self.assertRaises(ExternalApiError) as context:
                await client.get_json("https://example.test", provider="odsay")
            self.assertEqual(context.exception.provider, "odsay")
        finally:
            await client.close()