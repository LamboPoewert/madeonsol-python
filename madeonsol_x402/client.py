"""MadeOnSol API client. Supports API key, RapidAPI, or x402 micropayments."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

BASE_URL = "https://madeonsol.com"
RAPIDAPI_HOST = "madeonsol-solana-kol-tracker-tools-api.p.rapidapi.com"


class MadeOnSolClient:
    """MadeOnSol Solana API client.

    Auth priority: api_key > rapidapi_key > private_key (x402).

    Args:
        api_key: MadeOnSol API key (get one free at madeonsol.com/developer). Preferred.
        rapidapi_key: RapidAPI subscription key.
        private_key: Base58-encoded Solana private key for x402 USDC micropayments (AI agents).
        base_url: API base URL (default: https://madeonsol.com).
    """

    def __init__(
        self,
        private_key: str | None = None,
        base_url: str = BASE_URL,
        *,
        api_key: str | None = None,
        rapidapi_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._auth_mode: str = "none"
        self._auth_headers: dict[str, str] = {}
        self._x402: Any = None

        if api_key:
            self._auth_mode = "madeonsol"
            self._auth_headers = {"Authorization": f"Bearer {api_key}"}
        elif rapidapi_key:
            self._auth_mode = "rapidapi"
            self._auth_headers = {
                "x-rapidapi-key": rapidapi_key,
                "x-rapidapi-host": RAPIDAPI_HOST,
            }
        elif private_key:
            self._auth_mode = "x402"
            from x402 import x402Client
            from x402.mechanisms.svm import KeypairSigner
            from x402.mechanisms.svm.exact.register import register_exact_svm_client
            self._x402 = x402Client()
            signer = KeypairSigner.from_base58(private_key)
            register_exact_svm_client(self._x402, signer)
        else:
            raise ValueError(
                "Provide api_key, rapidapi_key, or private_key. "
                "Get a free API key at madeonsol.com/developer"
            )

    def _resolve_path(self, path: str) -> str:
        if self._auth_mode in ("madeonsol", "rapidapi"):
            return path.replace("/api/x402/", "/api/v1/")
        return path

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        api_path = self._resolve_path(path)
        if self._auth_mode == "x402":
            from x402.http.clients import x402HttpxClient
            async with x402HttpxClient(self._x402) as http:
                resp = await http.get(f"{self.base_url}{api_path}", params=params)
                resp.raise_for_status()
                return resp.json()
        else:
            async with httpx.AsyncClient() as http:
                resp = await http.get(
                    f"{self.base_url}{api_path}",
                    params=params,
                    headers=self._auth_headers,
                )
                resp.raise_for_status()
                return resp.json()

    def _get_sync(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, self._get(path, params)).result()
        return asyncio.run(self._get(path, params))

    # ── Endpoints ──

    def kol_feed(
        self, *, limit: int = 50, action: str | None = None, kol: str | None = None
    ) -> dict[str, Any]:
        """Real-time KOL trade feed from 946+ wallets."""
        params: dict[str, Any] = {"limit": limit}
        if action:
            params["action"] = action
        if kol:
            params["kol"] = kol
        return self._get_sync("/api/x402/kol/feed", params)

    def kol_coordination(
        self, *, period: str = "24h", min_kols: int = 3, limit: int = 20
    ) -> dict[str, Any]:
        """KOL convergence signals."""
        return self._get_sync("/api/x402/kol/coordination", {
            "period": period, "min_kols": min_kols, "limit": limit,
        })

    def kol_leaderboard(self, *, period: str = "7d", limit: int = 20) -> dict[str, Any]:
        """KOL PnL/win-rate rankings."""
        return self._get_sync("/api/x402/kol/leaderboard", {
            "period": period, "limit": limit,
        })

    def deployer_alerts(
        self, *, limit: int = 20, since: str | None = None, offset: int = 0
    ) -> dict[str, Any]:
        """Elite Pump.fun deployer alerts."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if since:
            params["since"] = since
        return self._get_sync("/api/x402/deployer-hunter/alerts", params)

    def discovery(self) -> dict[str, Any]:
        """Free — list all endpoints and prices."""
        resp = httpx.get(f"{self.base_url}/api/x402")
        resp.raise_for_status()
        return resp.json()


class MadeOnSolREST:
    """REST API client for webhook management and WebSocket streaming tokens.

    Args:
        api_key: MadeOnSol API key (preferred) or RapidAPI key.
        rapidapi_key: RapidAPI subscription key (alternative).
        base_url: API base URL (default: https://madeonsol.com).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        *,
        rapidapi_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        if api_key and api_key.startswith("msk_"):
            self._headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        elif api_key:
            # Legacy: treat non-msk_ key as RapidAPI key for backwards compat
            self._headers = {
                "Content-Type": "application/json",
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": RAPIDAPI_HOST,
            }
        elif rapidapi_key:
            self._headers = {
                "Content-Type": "application/json",
                "x-rapidapi-key": rapidapi_key,
                "x-rapidapi-host": RAPIDAPI_HOST,
            }
        else:
            raise ValueError(
                "Provide api_key or rapidapi_key. "
                "Get a free API key at madeonsol.com/developer"
            )

    def _request(self, method: str, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = httpx.request(
            method,
            f"{self.base_url}/api/v1{path}",
            headers=self._headers,
            json=json_body,
        )
        resp.raise_for_status()
        return resp.json()

    def create_webhook(
        self,
        *,
        url: str,
        events: list[str],
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a webhook. Returns webhook with HMAC secret (shown once)."""
        body: dict[str, Any] = {"url": url, "events": events}
        if filters:
            body["filters"] = filters
        return self._request("POST", "/webhooks", body)

    def list_webhooks(self) -> dict[str, Any]:
        """List all your registered webhooks."""
        return self._request("GET", "/webhooks")

    def get_webhook(self, webhook_id: int) -> dict[str, Any]:
        """Get webhook detail with recent delivery log."""
        return self._request("GET", f"/webhooks/{webhook_id}")

    def update_webhook(self, webhook_id: int, **kwargs: Any) -> dict[str, Any]:
        """Update a webhook (url, events, filters, is_active)."""
        return self._request("PATCH", f"/webhooks/{webhook_id}", kwargs)

    def delete_webhook(self, webhook_id: int) -> dict[str, Any]:
        """Delete a webhook permanently."""
        return self._request("DELETE", f"/webhooks/{webhook_id}")

    def test_webhook(self, webhook_id: int) -> dict[str, Any]:
        """Send a test payload to verify a webhook URL."""
        return self._request("POST", "/webhooks/test", {"webhook_id": webhook_id})

    def get_stream_token(self) -> dict[str, Any]:
        """Generate a 24h WebSocket streaming token."""
        return self._request("POST", "/stream/token")
