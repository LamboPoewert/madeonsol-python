# madeonsol-x402

Python SDK for the [MadeOnSol](https://madeonsol.com) Solana KOL intelligence API.

## Authentication

Three options (in priority order):

| Method | Parameter / Env var | Best for |
|---|---|---|
| **MadeOnSol API key** (recommended) | `api_key` / `MADEONSOL_API_KEY` | Developers — [get a free key](https://madeonsol.com/developer) |
| RapidAPI key | `rapidapi_key` / `RAPIDAPI_KEY` | RapidAPI subscribers |
| x402 micropayments | `private_key` / `SVM_PRIVATE_KEY` | AI agents with Solana wallets |

## Install

```bash
pip install madeonsol-x402                    # core SDK
pip install madeonsol-x402[langchain]         # + LangChain tools
pip install madeonsol-x402[crewai]            # + CrewAI tools
```

> x402 dependencies are only needed when using `private_key` / `SVM_PRIVATE_KEY`.

## Quick Start

```python
from madeonsol_x402 import MadeOnSolClient

# Option 1: API key (simplest — get one free at madeonsol.com/developer)
client = MadeOnSolClient(api_key="msk_your_api_key_here")

# Option 2: RapidAPI key
# client = MadeOnSolClient(rapidapi_key="your_rapidapi_key")

# Option 3: x402 micropayments (AI agents)
# client = MadeOnSolClient(private_key="your_solana_private_key_base58")

# Real-time KOL trades
trades = client.kol_feed(limit=10, action="buy")

# KOL convergence signals
signals = client.kol_coordination(period="24h", min_kols=3)

# KOL leaderboard
leaders = client.kol_leaderboard(period="7d")

# Deployer alerts
alerts = client.deployer_alerts(limit=10)

# Free discovery endpoint
info = client.discovery()
```

## LangChain

```python
from madeonsol_x402.langchain_tools import ALL_TOOLS

# Set MADEONSOL_API_KEY, RAPIDAPI_KEY, or SVM_PRIVATE_KEY env var
agent = create_react_agent(llm, tools=ALL_TOOLS)
```

## CrewAI

```python
from madeonsol_x402.crewai_tools import ALL_TOOLS

agent = Agent(role="Solana Analyst", tools=ALL_TOOLS)
```

## Endpoints

| Method | Description |
|---|---|
| `kol_feed()` | Real-time KOL trade feed (946 wallets) |
| `kol_coordination()` | Multi-KOL convergence signals |
| `kol_leaderboard()` | PnL and win rate rankings |
| `deployer_alerts()` | Elite Pump.fun deployer launches |
| `discovery()` | List all endpoints and prices (free) |

## Also Available

| Platform | Package |
|---|---|
| TypeScript SDK | [`madeonsol-x402`](https://www.npmjs.com/package/madeonsol-x402) |
| MCP Server (Claude, Cursor) | [`mcp-server-madeonsol`](https://www.npmjs.com/package/mcp-server-madeonsol) |
| ElizaOS | [`@madeonsol/plugin-madeonsol`](https://www.npmjs.com/package/@madeonsol/plugin-madeonsol) |
| Solana Agent Kit | [`solana-agent-kit-plugin-madeonsol`](https://www.npmjs.com/package/solana-agent-kit-plugin-madeonsol) |

## License

MIT
