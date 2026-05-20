"""MadeOnSol SDK — Solana KOL intelligence. Supports MadeOnSol API key (msk_) or x402 micropayments."""

from .client import MadeOnSolClient, MadeOnSolREST

__all__ = ["MadeOnSolClient", "MadeOnSolREST"]
__version__ = "1.8.0"
