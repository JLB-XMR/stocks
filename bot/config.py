"""Bot configuration.

Tickers, target weights, drift threshold, and environment variable loading.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    # IBKR Gateway
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 4001
    ibkr_client_id: int = 1

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Portfolio targets (VCI)
    tickers: list[str] = field(default_factory=lambda: [
        "VZ", "C", "CMCSA", "PBR", "PLAB", "IPGP", "AGCO", "CNH", "TRMB",
    ])
    target_weights: dict[str, float] = field(default_factory=lambda: {
        "VZ": 0.126,
        "C": 0.091,
        "CMCSA": 0.105,
        "PBR": 0.101,
        "PLAB": 0.088,
        "IPGP": 0.096,
        "AGCO": 0.096,
        "CNH": 0.095,
        "TRMB": 0.096,
        "CASH": 0.107,
    })

    # Rebalancing
    drift_threshold: float = 0.05  # 5%
    rebalance_time: str = "09:30"  # EST

    # Guardrails
    max_position_pct: float = 0.15  # No single order >15% of portfolio
    daily_loss_limit: float = 0.03  # Kill switch at -3% daily
    dry_run: bool = True  # Default to dry run
    limit_orders_only: bool = True  # Never market orders

    # Database
    db_path: str = "trades.db"

    @classmethod
    def from_env(cls) -> "BotConfig":
        """Load configuration from environment variables."""
        return cls(
            ibkr_host=os.getenv("IBKR_HOST", "127.0.0.1"),
            ibkr_port=int(os.getenv("IBKR_PORT", "4001")),
            ibkr_client_id=int(os.getenv("IBKR_CLIENT_ID", "1")),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            dry_run=os.getenv("DRY_RUN", "true").lower() == "true",
            db_path=os.getenv("DB_PATH", "trades.db"),
        )
