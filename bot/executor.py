"""Order executor with SQLite logging.

Limit orders only. Includes dry-run mode and all mandatory guardrails.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from bot.config import BotConfig
from bot.engine import Trade

logger = logging.getLogger(__name__)


class TradeLogger:
    """SQLite trade logger."""

    def __init__(self, db_path: str = "trades.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    action TEXT NOT NULL,
                    shares INTEGER NOT NULL,
                    estimated_value REAL NOT NULL,
                    reason TEXT,
                    status TEXT NOT NULL,
                    order_id TEXT,
                    dry_run BOOLEAN NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_pnl (
                    date TEXT PRIMARY KEY,
                    start_value REAL NOT NULL,
                    end_value REAL,
                    pnl_pct REAL,
                    kill_switch_triggered BOOLEAN DEFAULT FALSE
                )
            """)

    def log_trade(
        self,
        trade: Trade,
        status: str,
        order_id: str = "",
        dry_run: bool = True,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO trades
                   (timestamp, ticker, action, shares, estimated_value, reason, status, order_id, dry_run)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(),
                    trade.ticker,
                    trade.action,
                    trade.shares,
                    trade.estimated_value,
                    trade.reason,
                    status,
                    order_id,
                    dry_run,
                ),
            )

    def log_daily_pnl(self, start_value: float, end_value: float | None = None) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        pnl_pct = ((end_value - start_value) / start_value * 100) if end_value else None
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO daily_pnl (date, start_value, end_value, pnl_pct)
                   VALUES (?, ?, ?, ?)""",
                (today, start_value, end_value, pnl_pct),
            )

    def get_recent_trades(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]


class OrderExecutor:
    """Execute trades via IBKR Gateway. Limit orders only."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.trade_logger = TradeLogger(config.db_path)
        self._ib = None

    async def connect(self) -> None:
        """Connect to IBKR for order execution."""
        try:
            from ib_async import IB
            self._ib = IB()
            await self._ib.connectAsync(
                self.config.ibkr_host,
                self.config.ibkr_port,
                clientId=self.config.ibkr_client_id + 1,  # different client ID
            )
        except ImportError:
            raise RuntimeError("ib_async required for live execution")

    async def execute_trades(self, trades: list[Trade]) -> list[dict]:
        """Execute a list of trades. Respects dry_run and guardrails.

        Returns list of execution results.
        """
        results = []

        for trade in trades:
            # Guardrail: check market hours (simplified)
            now = datetime.now()
            if now.hour < 9 or (now.hour == 9 and now.minute < 30) or now.hour >= 16:
                logger.warning("Outside market hours — skipping %s", trade.ticker)
                self.trade_logger.log_trade(trade, "SKIPPED_HOURS", dry_run=True)
                results.append({"trade": trade, "status": "SKIPPED_HOURS"})
                continue

            if self.config.dry_run:
                logger.info("[DRY RUN] %s %d %s (~$%.0f) — %s",
                            trade.action, trade.shares, trade.ticker,
                            trade.estimated_value, trade.reason)
                self.trade_logger.log_trade(trade, "DRY_RUN", dry_run=True)
                results.append({"trade": trade, "status": "DRY_RUN"})
                continue

            # Live execution with limit orders
            result = await self._place_limit_order(trade)
            results.append(result)

        return results

    async def _place_limit_order(self, trade: Trade) -> dict:
        """Place a limit order via IBKR."""
        if not self._ib or not self._ib.isConnected():
            raise ConnectionError("Not connected to IBKR for execution")

        from ib_async import LimitOrder, Stock

        contract = Stock(trade.ticker, "SMART", "USD")
        await self._ib.qualifyContractsAsync(contract)

        # Get current price for limit
        ticker_data = self._ib.reqMktData(contract)
        await self._ib.sleep(2)  # wait for data

        if trade.action == "BUY":
            # Limit at ask price (or last if ask unavailable)
            limit_price = ticker_data.ask if ticker_data.ask > 0 else ticker_data.last
            order = LimitOrder("BUY", trade.shares, limit_price)
        else:
            limit_price = ticker_data.bid if ticker_data.bid > 0 else ticker_data.last
            order = LimitOrder("SELL", trade.shares, limit_price)

        placed = self._ib.placeOrder(contract, order)
        logger.info("Placed %s order: %s %d %s @ $%.2f",
                     trade.action, trade.action, trade.shares, trade.ticker, limit_price)

        self.trade_logger.log_trade(
            trade, "PLACED", order_id=str(placed.order.orderId), dry_run=False,
        )

        return {"trade": trade, "status": "PLACED", "order_id": placed.order.orderId}

    def check_daily_loss_limit(self, start_value: float, current_value: float) -> bool:
        """Check if daily loss limit has been breached. Returns True if kill switch triggered."""
        if start_value <= 0:
            return False
        loss_pct = (start_value - current_value) / start_value
        if loss_pct > self.config.daily_loss_limit:
            logger.critical(
                "KILL SWITCH: Daily loss %.1f%% exceeds %.1f%% limit",
                loss_pct * 100, self.config.daily_loss_limit * 100,
            )
            return True
        return False
