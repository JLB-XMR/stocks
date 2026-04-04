"""Rebalance engine for the IBKR bot.

Calculates drift from target weights and generates a trade list.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from bot.config import BotConfig
from bot.connector import PortfolioSnapshot

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    ticker: str
    action: str  # "BUY" or "SELL"
    shares: int
    estimated_value: float
    reason: str


@dataclass
class RebalanceResult:
    max_drift: float
    needs_rebalance: bool
    trades: list[Trade]
    drifts: dict[str, float]  # ticker -> drift from target


def calculate_drift(
    snapshot: PortfolioSnapshot,
    config: BotConfig,
) -> RebalanceResult:
    """Calculate position drift from target weights.

    Args:
        snapshot: Current IBKR portfolio snapshot
        config: Bot configuration with target weights

    Returns:
        RebalanceResult with drift analysis and proposed trades
    """
    total = snapshot.total_value
    if total <= 0:
        return RebalanceResult(0, False, [], {})

    drifts: dict[str, float] = {}
    trades: list[Trade] = []

    for ticker, target_weight in config.target_weights.items():
        if ticker == "CASH":
            actual_weight = snapshot.cash / total
        elif ticker in snapshot.positions:
            actual_weight = snapshot.positions[ticker].market_value / total
        else:
            actual_weight = 0.0

        drift = actual_weight - target_weight
        drifts[ticker] = drift

    max_drift = max(abs(d) for d in drifts.values()) if drifts else 0
    needs_rebalance = max_drift > config.drift_threshold

    if needs_rebalance:
        trades = _generate_trades(snapshot, config, drifts)

    return RebalanceResult(
        max_drift=max_drift,
        needs_rebalance=needs_rebalance,
        trades=trades,
        drifts=drifts,
    )


def _generate_trades(
    snapshot: PortfolioSnapshot,
    config: BotConfig,
    drifts: dict[str, float],
) -> list[Trade]:
    """Generate trade list to return to target weights."""
    total = snapshot.total_value
    trades: list[Trade] = []

    for ticker, drift in drifts.items():
        if ticker == "CASH":
            continue
        if abs(drift) < 0.005:  # ignore sub-0.5% drifts
            continue

        target_value = total * config.target_weights.get(ticker, 0)
        current_value = (
            snapshot.positions[ticker].market_value
            if ticker in snapshot.positions
            else 0
        )
        diff = target_value - current_value

        # Guardrail: cap single order at max_position_pct of portfolio
        max_order = total * config.max_position_pct
        if abs(diff) > max_order:
            logger.warning(
                "%s trade capped: $%.0f -> $%.0f (max $%.0f)",
                ticker, diff, max_order if diff > 0 else -max_order, max_order,
            )
            diff = max_order if diff > 0 else -max_order

        # Estimate per-share price
        if ticker in snapshot.positions and snapshot.positions[ticker].shares > 0:
            estimated_price = current_value / snapshot.positions[ticker].shares
        elif ticker in snapshot.positions:
            estimated_price = snapshot.positions[ticker].avg_cost
        else:
            estimated_price = 0

        if diff > 0:
            shares = int(diff / estimated_price) if estimated_price > 0 else 0
            if shares > 0:
                trades.append(Trade(
                    ticker=ticker,
                    action="BUY",
                    shares=shares,
                    estimated_value=diff,
                    reason=f"Underweight by {abs(drift):.1%}",
                ))
        elif diff < 0:
            shares = int(abs(diff) / estimated_price) if estimated_price > 0 else 0
            if shares > 0:
                trades.append(Trade(
                    ticker=ticker,
                    action="SELL",
                    shares=shares,
                    estimated_value=abs(diff),
                    reason=f"Overweight by {abs(drift):.1%}",
                ))

    return trades
