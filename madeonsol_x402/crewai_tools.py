"""CrewAI tools for MadeOnSol API. Install: pip install madeonsol-x402[crewai]"""

from __future__ import annotations

import json
import os
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .client import MadeOnSolClient, MadeOnSolREST


def _client() -> MadeOnSolClient:
    """Create client using env vars. Priority: MADEONSOL_API_KEY > SVM_PRIVATE_KEY."""
    api_key = os.environ.get("MADEONSOL_API_KEY", "")
    private_key = os.environ.get("SVM_PRIVATE_KEY", "")
    if api_key:
        return MadeOnSolClient(api_key=api_key)
    if private_key:
        return MadeOnSolClient(private_key=private_key)
    raise ValueError(
        "Set MADEONSOL_API_KEY — free at https://madeonsol.com/pricing — or SVM_PRIVATE_KEY"
    )


def _rest_client() -> MadeOnSolREST:
    """Create REST client for webhooks/streaming. Requires MADEONSOL_API_KEY."""
    api_key = os.environ.get("MADEONSOL_API_KEY", "")
    if api_key:
        return MadeOnSolREST(api_key=api_key)
    raise ValueError(
        "Set MADEONSOL_API_KEY — free at https://madeonsol.com/pricing — for webhook/streaming features"
    )


class KolFeedInput(BaseModel):
    limit: int = Field(default=10, description="Number of trades (1-100)")
    action: str | None = Field(default=None, description="Filter: 'buy' or 'sell'")


class MadeOnSolKolFeed(BaseTool):
    name: str = "MadeOnSol KOL Feed"
    description: str = "Get real-time Solana KOL trades from 1,000+ tracked wallets via MadeOnSol. Costs $0.005 USDC per request."
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
    period: str = Field(
        default="7d",
        description="Time period: today, 7d, 30d, 90d, or 180d (180-day retention)",
    )
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
    tier: str | None = Field(
        default=None,
        description="Filter by deployer tier: elite, good, moderate, rising, or cold. PRO/ULTRA only — BASIC callers receive 403.",
    )


class MadeOnSolDeployerAlerts(BaseTool):
    name: str = "MadeOnSol Deployer Alerts"
    description: str = (
        "Get Pump.fun deployer launch alerts with KOL buy enrichment. "
        "PRO/ULTRA subscribers can filter by deployer tier. Costs $0.01 USDC per request."
    )
    args_schema: type[BaseModel] = DeployerAlertsInput

    def _run(self, limit: int = 10, tier: str | None = None) -> str:
        data = _client().deployer_alerts(limit=limit, tier=tier)
        return json.dumps(data, indent=2)


class CreateWebhookInput(BaseModel):
    url: str = Field(description="HTTPS webhook URL to receive events")
    events: str = Field(description="Comma-separated event types: kol:trade, deployer:alert, deployer:bond, kol:coordination")
    min_sol: float | None = Field(default=None, description="Optional: minimum SOL amount filter")


class MadeOnSolCreateWebhook(BaseTool):
    name: str = "MadeOnSol Create Webhook"
    description: str = "Register a webhook to receive real-time push notifications for KOL trades and deployer alerts. Requires MADEONSOL_API_KEY."
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
    description: str = "List all your registered MadeOnSol webhooks. Requires MADEONSOL_API_KEY."
    args_schema: type[BaseModel] = ListWebhooksInput

    def _run(self) -> str:
        data = _rest_client().list_webhooks()
        return json.dumps(data, indent=2)


class StreamTokenInput(BaseModel):
    pass


class MadeOnSolStreamToken(BaseTool):
    name: str = "MadeOnSol Stream Token"
    description: str = "Get a 24h WebSocket streaming token for real-time event streaming from MadeOnSol. Requires MADEONSOL_API_KEY."
    args_schema: type[BaseModel] = StreamTokenInput

    def _run(self) -> str:
        data = _rest_client().get_stream_token()
        return json.dumps(data, indent=2)


class StreamSessionsInput(BaseModel):
    pass


class MadeOnSolStreamSessions(BaseTool):
    name: str = "MadeOnSol Stream Sessions"
    description: str = "List your live WebSocket sessions (id, service, tier, channels, connected_at, messages_sent) across both stream services. Requires MADEONSOL_API_KEY (PRO/ULTRA)."
    args_schema: type[BaseModel] = StreamSessionsInput

    def _run(self) -> str:
        data = _rest_client().stream_sessions()
        return json.dumps(data, indent=2)


class KillStreamSessionInput(BaseModel):
    session_id: int = Field(description="The session id (positive integer) from stream_sessions to evict")


class MadeOnSolKillStreamSession(BaseTool):
    name: str = "MadeOnSol Kill Stream Session"
    description: str = "Force-terminate one of your live WebSocket sessions and free its connection slot — self-serve fix for a 4002 connection-limit lockout. Requires MADEONSOL_API_KEY (PRO/ULTRA)."
    args_schema: type[BaseModel] = KillStreamSessionInput

    def _run(self, session_id: int) -> str:
        data = _rest_client().kill_stream_session(session_id)
        return json.dumps(data, indent=2)


class PriceAlertCreateInput(BaseModel):
    token_mint: str = Field(description="Solana mint address (base58)")
    drop_pct: float = Field(description="Drop % threshold (0.01-99.99)")
    recovery_pct: float | None = Field(default=None, description="Recovery % (0.01-1000). Optional.")
    name: str | None = Field(default=None, description="Optional label")


class MadeOnSolPriceAlertCreate(BaseTool):
    name: str = "MadeOnSol Price Alert Create"
    description: str = "Create a price alert that fires when a token's MC drops by a specified %. Requires MADEONSOL_API_KEY (PRO/ULTRA)."
    args_schema: type[BaseModel] = PriceAlertCreateInput

    def _run(self, token_mint: str, drop_pct: float, recovery_pct: float | None = None, name: str | None = None) -> str:
        data = _rest_client().price_alerts_create(
            token_mint=token_mint, drop_pct=drop_pct,
            recovery_pct=recovery_pct, name=name,
        )
        return json.dumps(data, indent=2)


class PriceAlertsListInput(BaseModel):
    pass


class MadeOnSolPriceAlertsList(BaseTool):
    name: str = "MadeOnSol Price Alerts List"
    description: str = "List your price alerts. Requires MADEONSOL_API_KEY (PRO/ULTRA)."
    args_schema: type[BaseModel] = PriceAlertsListInput

    def _run(self) -> str:
        data = _rest_client().price_alerts_list()
        return json.dumps(data, indent=2)


class PriceAlertEventsInput(BaseModel):
    alert_id: int | None = Field(default=None, description="Filter to a specific alert")
    event_type: str | None = Field(default=None, description="'dip' or 'recovery'")
    limit: int | None = Field(default=None, description="Max events to return")


class MadeOnSolPriceAlertEvents(BaseTool):
    name: str = "MadeOnSol Price Alert Events"
    description: str = "Fired price alert event history (30-day retention). Requires MADEONSOL_API_KEY (PRO/ULTRA)."
    args_schema: type[BaseModel] = PriceAlertEventsInput

    def _run(self, alert_id: int | None = None, event_type: str | None = None, limit: int | None = None) -> str:
        data = _rest_client().price_alerts_events(
            alert_id=alert_id, event_type=event_type, limit=limit,
        )
        return json.dumps(data, indent=2)


class ScoutLeaderboardInput(BaseModel):
    limit: int | None = Field(default=None, description="Max entries to return")
    scout_tier: str | None = Field(default=None, description="Filter: S, A, B, or C")


class MadeOnSolScoutLeaderboard(BaseTool):
    name: str = "MadeOnSol Scout Leaderboard"
    description: str = "Scout leaderboard — top KOLs ranked by scout score and swarm attraction rate. ULTRA only."
    args_schema: type[BaseModel] = ScoutLeaderboardInput

    def _run(self, limit: int | None = None, scout_tier: str | None = None) -> str:
        data = _rest_client().scout_leaderboard(limit=limit, scout_tier=scout_tier)
        return json.dumps(data, indent=2)


class TokenFlowInput(BaseModel):
    mint: str = Field(description="Token mint address (base58)")
    window: str = Field(default="1h", description="Rolling window: '1h' or '24h'")


class MadeOnSolTokenFlow(BaseTool):
    name: str = "MadeOnSol Token Flow"
    description: str = "Token money-flow over a rolling window: unique wallets/buyers/sellers, buy/sell counts, buy/sell SOL, net SOL flow, trades per wallet. PRO+."
    args_schema: type[BaseModel] = TokenFlowInput

    def _run(self, mint: str, window: str = "1h") -> str:
        data = _client().token_flow(mint, window=window)
        return json.dumps(data, indent=2)


class KolConsensusInput(BaseModel):
    mint: str = Field(description="Token mint address (base58)")


class MadeOnSolKolConsensus(BaseTool):
    name: str = "MadeOnSol KOL Consensus"
    description: str = "KOL consensus on a token: buyers/sellers, exit rate, net flow, median entry MC."
    args_schema: type[BaseModel] = KolConsensusInput

    def _run(self, mint: str) -> str:
        data = _rest_client().kol_consensus(mint)
        return json.dumps(data, indent=2)


class PeakHistoryInput(BaseModel):
    mint: str = Field(description="Token mint address (base58)")


class MadeOnSolPeakHistory(BaseTool):
    name: str = "MadeOnSol Peak History"
    description: str = "Peak MC history: ATH, decline from peak %, MC at bond and at 1h/6h/24h/7d after bond."
    args_schema: type[BaseModel] = PeakHistoryInput

    def _run(self, mint: str) -> str:
        data = _rest_client().peak_history(mint)
        return json.dumps(data, indent=2)


class AlmostBondedInput(BaseModel):
    min_progress: float | None = Field(default=None, description="Lower bound on bonding progress % (default 80)")
    min_velocity_pct_per_min: float | None = Field(default=None, description="Minimum Δprogress/min; drops tokens without a 5m snapshot")
    deployer_tier: str | None = Field(default=None, description="Filter by deployer tier: elite/good/moderate/rising/cold/unranked")
    sort: str | None = Field(default=None, description="velocity_desc (default), progress_desc, or eta_asc")
    limit: int | None = Field(default=None, description="Page size (1-100, default 50)")


class MadeOnSolAlmostBonded(BaseTool):
    name: str = "MadeOnSol Almost Bonded"
    description: str = "Pre-bond pump.fun tokens near graduation, ranked by velocity (Δprogress/min): progress_pct, velocity_pct_per_min, eta_minutes, stalled, deployer_tier. PRO+."
    args_schema: type[BaseModel] = AlmostBondedInput

    def _run(
        self,
        min_progress: float | None = None,
        min_velocity_pct_per_min: float | None = None,
        deployer_tier: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
    ) -> str:
        data = _rest_client().almost_bonded(
            min_progress=min_progress,
            min_velocity_pct_per_min=min_velocity_pct_per_min,
            deployer_tier=deployer_tier,
            sort=sort,
            limit=limit,
        )
        return json.dumps(data, indent=2)


ALL_TOOLS = [
    MadeOnSolKolFeed(),
    MadeOnSolKolCoordination(),
    MadeOnSolKolLeaderboard(),
    MadeOnSolDeployerAlerts(),
    MadeOnSolCreateWebhook(),
    MadeOnSolListWebhooks(),
    MadeOnSolStreamToken(),
    MadeOnSolStreamSessions(),
    MadeOnSolKillStreamSession(),
    MadeOnSolPriceAlertCreate(),
    MadeOnSolPriceAlertsList(),
    MadeOnSolPriceAlertEvents(),
    MadeOnSolScoutLeaderboard(),
    MadeOnSolTokenFlow(),
    MadeOnSolKolConsensus(),
    MadeOnSolPeakHistory(),
    MadeOnSolAlmostBonded(),
]
