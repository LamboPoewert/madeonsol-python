# madeonsol-x402

Python SDK for the [MadeOnSol](https://madeonsol.com) Solana KOL intelligence API. Pay-per-request with USDC on Solana via the x402 protocol.

## Install

```bash
pip install madeonsol-x402                    # core SDK
pip install madeonsol-x402[langchain]         # + LangChain tools
pip install madeonsol-x402[crewai]            # + CrewAI tools
```

## Quick Start

```python
from madeonsol_x402 import MadeOnSolClient

client = MadeOnSolClient("your_solana_private_key_base58")

# Real-time KOL trades ($0.005/req)
trades = client.kol_feed(limit=10, action="buy")

# KOL convergence signals ($0.02/req)
signals = client.kol_coordination(period="24h", min_kols=3)

# KOL leaderboard ($0.005/req)
leaders = client.kol_leaderboard(period="7d")

# Deployer alerts ($0.01/req)
alerts = client.deployer_alerts(limit=10)

# Free discovery endpoint
info = client.discovery()
```

## LangChain

```python
from madeonsol_x402.langchain_tools import ALL_TOOLS

# Add to your LangChain agent
agent = create_react_agent(llm, tools=ALL_TOOLS)
```

Set `SVM_PRIVATE_KEY` env var for automatic x402 payments.

## CrewAI

```python
from madeonsol_x402.crewai_tools import ALL_TOOLS

agent = Agent(role="Solana Analyst", tools=ALL_TOOLS)
```

## Endpoints

| Method | Price | Description |
|---|---|---|
| `kol_feed()` | $0.005 | Real-time KOL trade feed (946 wallets) |
| `kol_coordination()` | $0.02 | Multi-KOL convergence signals |
| `kol_leaderboard()` | $0.005 | PnL and win rate rankings |
| `deployer_alerts()` | $0.01 | Elite Pump.fun deployer launches |
| `discovery()` | Free | List all endpoints and prices |

## How It Works

The SDK uses the [x402 payment protocol](https://x402.org). When you call an endpoint, the library automatically handles the 402 → sign USDC → retry flow. Your wallet needs USDC on Solana mainnet.

## License

MIT
