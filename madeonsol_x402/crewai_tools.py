"""CrewAI tools for MadeOnSol x402 API. Install: pip install madeonsol-x402[crewai]"""

from __future__ import annotations

import json
import os
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .client import MadeOnSolClient


def _client() -> MadeOnSolClient:
    key = os.environ.get("SVM_PRIVATE_KEY", "")
    if not key:
        raise ValueError("Set SVM_PRIVATE_KEY env var for x402 payments")
    return MadeOnSolClient(key)


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


ALL_TOOLS = [
    MadeOnSolKolFeed(),
    MadeOnSolKolCoordination(),
    MadeOnSolKolLeaderboard(),
    MadeOnSolDeployerAlerts(),
]
