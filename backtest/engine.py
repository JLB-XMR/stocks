"""Backtest engine for VCI Portfolio 1.

Simulates Oct 2024 -> Apr 2026 using the documented quarterly performance data.
Also provides a framework for running forward simulations with user-supplied prices.
"""

from dataclasses import dataclass

from data.models import BacktestQuarter, BacktestResult


# Historical quarterly data from the research document (simulated Oct 2024 - Apr 2026)
VCI_BACKTEST_QUARTERS = [
    BacktestQuarter("2024-10", 1000.0, 0.0, "Initial allocation"),
    BacktestQuarter("2025-01", 996.0, -0.4, "PBR -19%, Citi +15%"),
    BacktestQuarter("2025-04", 1025.0, 2.9, "Recovery + tariff noise absorbed"),
    BacktestQuarter("2025-07", 1066.0, 4.0, "AGCO/TRMB carry the quarter"),
    BacktestQuarter("2025-10", 1086.0, 1.9, "PLAB record IC revenue"),
    BacktestQuarter("2026-01", 1116.0, 2.8, "Portfolio high-water mark"),
    BacktestQuarter("2026-04", 1044.0, -6.4, "Liberation Day tariff shock"),
]

VCI_BACKTEST_WINNERS = {
    "C": 36.0,
    "VZ": 28.1,
    "AGCO": 19.7,
    "TRMB": 14.5,
}

VCI_BACKTEST_DETRACTORS = {
    "PLAB": -15.9,
    "CMCSA": -15.3,
    "IPGP": -12.9,
    "PBR": -6.6,
}


def get_vci_backtest() -> BacktestResult:
    """Return the documented VCI 18-month backtest results."""
    values = [q.portfolio_value for q in VCI_BACKTEST_QUARTERS]
    return BacktestResult(
        total_return=4.4,
        peak_value=max(values),
        trough_value=min(values),
        max_drawdown=-6.4,
        benchmark_return=-2.0,  # S&P 500 over same period
        quarters=VCI_BACKTEST_QUARTERS,
        winners=VCI_BACKTEST_WINNERS,
        detractors=VCI_BACKTEST_DETRACTORS,
    )


@dataclass
class QuarterSnapshot:
    """A single quarter's portfolio state during forward simulation."""
    date: str
    positions: dict[str, float]  # ticker -> market value
    cash: float
    total_value: float
    rebalanced: bool


def simulate_forward(
    initial_positions: dict[str, float],
    initial_cash: float,
    target_weights: dict[str, float],
    quarterly_returns: list[dict[str, float]],
    drift_threshold: float = 0.05,
) -> list[QuarterSnapshot]:
    """Run a forward simulation given projected quarterly returns per ticker.

    Args:
        initial_positions: ticker -> initial market value
        initial_cash: starting cash
        target_weights: ticker -> target weight (0-1), must include "CASH"
        quarterly_returns: list of dicts {ticker: return_pct} for each quarter
        drift_threshold: rebalance if any position drifts more than this

    Returns:
        List of QuarterSnapshot for each quarter
    """
    snapshots = []
    positions = dict(initial_positions)
    cash = initial_cash

    for q_idx, q_returns in enumerate(quarterly_returns):
        # Apply returns
        for ticker in positions:
            ret = q_returns.get(ticker, 0.0)
            positions[ticker] *= (1 + ret / 100.0)

        total = sum(positions.values()) + cash

        # Check drift and rebalance if needed
        rebalanced = False
        max_drift = 0.0
        for ticker, value in positions.items():
            actual_weight = value / total if total > 0 else 0
            target = target_weights.get(ticker, 0)
            drift = abs(actual_weight - target)
            max_drift = max(max_drift, drift)

        if max_drift > drift_threshold:
            # Rebalance to target weights
            for ticker in positions:
                target = target_weights.get(ticker, 0)
                positions[ticker] = total * target
            cash = total * target_weights.get("CASH", 0)
            rebalanced = True

        snapshots.append(QuarterSnapshot(
            date=f"Q{q_idx + 1}",
            positions=dict(positions),
            cash=cash,
            total_value=total,
            rebalanced=rebalanced,
        ))

    return snapshots


def calculate_scenario_returns(
    cost_bases: dict[str, float],
    cash: float,
    multipliers: dict[str, float],
) -> float:
    """Calculate portfolio-level return for a given scenario.

    Args:
        cost_bases: ticker -> cost basis
        cash: cash amount
        multipliers: ticker -> return multiplier (e.g., 100 = 100x)

    Returns:
        Portfolio-level return multiple
    """
    total_cost = sum(cost_bases.values()) + cash
    total_return = sum(
        cost_bases[t] * multipliers.get(t, 1.0) for t in cost_bases
    ) + cash

    return total_return / total_cost if total_cost > 0 else 0
