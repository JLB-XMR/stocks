"""IBKR Gateway connector.

Reads positions and market values from Interactive Brokers Gateway via ib_async.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PositionInfo:
    ticker: str
    shares: float
    market_value: float
    avg_cost: float
    unrealized_pnl: float


@dataclass
class PortfolioSnapshot:
    positions: dict[str, PositionInfo]
    total_value: float
    cash: float
    timestamp: str


class IBKRConnector:
    """Connects to IBKR Gateway and reads account data.

    Requires ib_async and a running IBKR Gateway instance.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 4001, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self._ib = None

    async def connect(self) -> None:
        """Establish connection to IBKR Gateway."""
        try:
            from ib_async import IB
            self._ib = IB()
            await self._ib.connectAsync(self.host, self.port, clientId=self.client_id)
            logger.info("Connected to IBKR Gateway at %s:%s", self.host, self.port)
        except ImportError:
            raise RuntimeError(
                "ib_async is required. Install with: pip install ib_async"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to IBKR Gateway: {e}")

    async def disconnect(self) -> None:
        """Disconnect from IBKR Gateway."""
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
            logger.info("Disconnected from IBKR Gateway")

    async def get_portfolio_snapshot(self) -> PortfolioSnapshot:
        """Read current positions, values, and cash from IBKR."""
        if not self._ib or not self._ib.isConnected():
            raise ConnectionError("Not connected to IBKR Gateway")

        from datetime import datetime

        account_values = self._ib.accountValues()
        portfolio_items = self._ib.portfolio()

        # Extract cash balance
        cash = 0.0
        total_value = 0.0
        for av in account_values:
            if av.tag == "CashBalance" and av.currency == "USD":
                cash = float(av.value)
            if av.tag == "NetLiquidation" and av.currency == "USD":
                total_value = float(av.value)

        # Extract positions
        positions: dict[str, PositionInfo] = {}
        for item in portfolio_items:
            ticker = item.contract.symbol
            positions[ticker] = PositionInfo(
                ticker=ticker,
                shares=item.position,
                market_value=item.marketValue,
                avg_cost=item.averageCost,
                unrealized_pnl=item.unrealizedPNL,
            )

        return PortfolioSnapshot(
            positions=positions,
            total_value=total_value,
            cash=cash,
            timestamp=datetime.now().isoformat(),
        )
