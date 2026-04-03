"""CrewAI tools for MadeOnSol x402 API. Install: pip install madeonsol-x402[crewai]"""

from __future__ import annotations

import json
import os
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .client import MadeOnSolClient, MadeOnSolREST


def _client() -> MadeOnSolClient:
    key = os.environ.get("SVM_PRIVATE_KEY", "")
    if not key:
        raise ValueError("Set SVM_PRIVATE_KEY env var for x402 payments")
    return MadeOnSolClient(key)


def _rest_client() -> MadeOnSolREST:
    key = os.environ.get("RAPIDAPI_KEY", "")
    if not key:
        raise ValueError("Set RAPIDAPI_KEY env var for webhook/streaming features")
    return MadeOnSolREST(key)


class KolFeedInput(BaseModel):
    limit: int = Field(default=10, description="Number of trades (1-100)")
    action: str | None = Field(default=None, description="Filter: 'buy' or 'sell'")


class MadeOnSolKolFeed(BaseTool):
    name: str = "MadeOnSol KOL Feed"
    description: str = "Get real-time Solana KOL trades from 946 tracked wallets via MadeOnSol. Costs $0.005 USDC per request."
    args_schema: type[BaseModel] = KolFeedInput

    def _run(self, limit: int = 10, action: str | None = None) -> str:
        data = _client().kol_feed(limit=limit, action=action)
        return json.dumps(data, indent=2)


class KolCoordinationInput(BaseModel):
    period: str = Field(default="24h", description="Time period: 1h, 6h, 24h, or 7d")
    min_kols: int = Field(default=3, description="Minimum KOLs converging (2-50)")


class MadeOnSolKolCoordination(BaseTool):
    name: str = "MadeOnSol KOL Coordination"
    description: str = "Get KOL convergence signals — tokens multiple KOLs are accumulating. Costs $0.02 USDC per request."
    args_schema: type[BaseModel] = KolCoordinationInput

    def _run(self, period: str = "24h", min_kols: int = 3) -> str:
        data = _client().kol_coordination(period=period, min_kols=min_kols)
        return json.dumps(data, indent=2)


class KolLeaderboardInput(BaseModel):
    period: str = Field(default="7d", description="Time period: today, 7d, or 30d")
    limit: int = Field(default=10, description="Number of KOLs (1-50)")


class MadeOnSolKolLeaderboard(BaseTool):
    name: str = "MadeOnSol KOL Leaderboard"
    description: str = "Get KOL performance rankings by PnL and win rate. Costs $0.005 USDC per request."
    args_schema: type[BaseModel] = KolLeaderboardInput

    def _run(self, period: str = "7d", limit: int = 10) -> str:
        data = _client().kol_leaderboard(period=period, limit=limit)
        return json.dumps(data, indent=2)


class DeployerAlertsInput(BaseModel):
    limit: int = Field(default=10, description="Number of alerts (1-100)")


class MadeOnSolDeployerAlerts(BaseTool):
    name: str = "MadeOnSol Deployer Alerts"
    description: str = "Get elite Pump.fun deployer launch alerts with KOL buy enrichment. Costs $0.01 USDC per request."
    args_schema: type[BaseModel] = DeployerAlertsInput

    def _run(self, limit: int = 10) -> str:
        data = _client().deployer_alerts(limit=limit)
        return json.dumps(data, indent=2)


class CreateWebhookInput(BaseModel):
    url: str = Field(description="HTTPS webhook URL to receive events")
    events: str = Field(description="Comma-separated event types: kol:trade, deployer:alert, deployer:bond, kol:coordination")
    min_sol: float | None = Field(default=None, description="Optional: minimum SOL amount filter")


class MadeOnSolCreateWebhook(BaseTool):
    name: str = "MadeOnSol Create Webhook"
    description: str = "Register a webhook to receive real-time push notifications for KOL trades and deployer alerts. Requires RAPIDAPI_KEY."
    args_schema: type[BaseModel] = CreateWebhookInput

    def _run(self, url: str, events: str, min_sol: float | None = None) -> str:
        filters = {}
        if min_sol:
            filters["min_sol"] = min_sol
        data = _rest_client().create_webhook(url=url, events=events.split(","), filters=filters or None)
        return json.dumps(data, indent=2)


class ListWebhooksInput(BaseModel):
    pass


class MadeOnSolListWebhooks(BaseTool):
    name: str = "MadeOnSol List Webhooks"
    description: str = "List all your registered MadeOnSol webhooks. Requires RAPIDAPI_KEY."
    args_schema: type[BaseModel] = ListWebhooksInput

    def _run(self) -> str:
        data = _rest_client().list_webhooks()
        return json.dumps(data, indent=2)


class StreamTokenInput(BaseModel):
    pass


class MadeOnSolStreamToken(BaseTool):
    name: str = "MadeOnSol Stream Token"
    description: str = "Get a 24h WebSocket streaming token for real-time event streaming from MadeOnSol. Requires RAPIDAPI_KEY."
    args_schema: type[BaseModel] = StreamTokenInput

    def _run(self) -> str:
        data = _rest_client().get_stream_token()
        return json.dumps(data, indent=2)


ALL_TOOLS = [
    MadeOnSolKolFeed(),
    MadeOnSolKolCoordination(),
    MadeOnSolKolLeaderboard(),
    MadeOnSolDeployerAlerts(),
    MadeOnSolCreateWebhook(),
    MadeOnSolListWebhooks(),
    MadeOnSolStreamToken(),
]
