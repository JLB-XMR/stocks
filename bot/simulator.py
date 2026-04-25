"""Bot simulation engine.

Replays historical quarterly price data through the full bot pipeline:
drift detection -> trade generation -> execution logging -> message formatting.

Also supports synthetic drift injection for edge-case testing.

Usage:
    python -m bot.simulator                     # Replay 6 historical quarters
    python -m bot.simulator --stress            # Run guardrail stress tests
    python -m bot.simulator --synthetic heavy    # Inject heavy synthetic drift
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import tempfile
from dataclasses import dataclass

from tabulate import tabulate

from bot.config import BotConfig
from bot.connector import PortfolioSnapshot, PositionInfo
from bot.engine import RebalanceResult, Trade, calculate_drift
from bot.executor import OrderExecutor, TradeLogger
from bot.notifier import (
    format_kill_switch_alert,
    format_rebalance_message,
    format_trade_confirmation,
)
from bot.sim_data import (
    ENTRY_PRICES,
    QUARTER_DATES,
    QUARTER_DRIVERS,
    QUARTERLY_PRICES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class SimQuarterResult:
    date: str
    driver: str
    portfolio_value: float
    cash: float
    max_drift: float
    needs_rebalance: bool
    trades: list[Trade]
    messages: list[str]


def build_snapshot_from_prices(
    prices: dict[str, float],
    shares: dict[str, float],
    cash: float,
) -> PortfolioSnapshot:
    """Build a PortfolioSnapshot from prices and share counts."""
    positions = {}
    total = cash
    for ticker, price in prices.items():
        if ticker not in shares:
            continue
        s = shares[ticker]
        mv = s * price
        entry = ENTRY_PRICES.get(ticker, price)
        positions[ticker] = PositionInfo(
            ticker=ticker,
            shares=s,
            market_value=mv,
            avg_cost=entry,
            unrealized_pnl=mv - (s * entry),
        )
        total += mv

    return PortfolioSnapshot(
        positions=positions,
        total_value=total,
        cash=cash,
        timestamp="SIM",
    )


def compute_initial_shares(config: BotConfig, total: float) -> dict[str, float]:
    """Compute initial share counts from target weights and entry prices."""
    shares = {}
    for ticker in config.tickers:
        weight = config.target_weights.get(ticker, 0)
        alloc = total * weight
        price = ENTRY_PRICES.get(ticker, 1)
        shares[ticker] = alloc / price
    return shares


def replay_historical(config: BotConfig) -> list[SimQuarterResult]:
    """Replay all 6 historical quarters through the bot pipeline."""
    total_portfolio = 1000.0
    cash_weight = config.target_weights.get("CASH", 0.107)
    cash = total_portfolio * cash_weight

    shares = compute_initial_shares(config, total_portfolio)
    results: list[SimQuarterResult] = []

    for i, date in enumerate(QUARTER_DATES):
        prices = QUARTERLY_PRICES[date]
        driver = QUARTER_DRIVERS[date]

        snapshot = build_snapshot_from_prices(prices, shares, cash)
        result = calculate_drift(snapshot, config)

        messages = []
        if result.needs_rebalance:
            messages.append(format_rebalance_message(result))
            messages.append(format_trade_confirmation(result.trades, dry_run=True))

            # Apply rebalancing: adjust shares to target weights
            for trade in result.trades:
                price = prices.get(trade.ticker, 1)
                if trade.action == "BUY":
                    shares[trade.ticker] = shares.get(trade.ticker, 0) + trade.shares
                    cash -= trade.shares * price
                else:
                    shares[trade.ticker] = shares.get(trade.ticker, 0) - trade.shares
                    cash += trade.shares * price

        results.append(SimQuarterResult(
            date=date,
            driver=driver,
            portfolio_value=snapshot.total_value,
            cash=cash,
            max_drift=result.max_drift,
            needs_rebalance=result.needs_rebalance,
            trades=result.trades,
            messages=messages,
        ))

    return results


# --- Synthetic Drift Injection ---

SYNTHETIC_SCENARIOS = {
    "mild": {
        "description": "Two positions drift modestly in opposite directions",
        "price_overrides": {"VZ": 62.00, "CMCSA": 21.00},
    },
    "heavy": {
        "description": "Two positions diverge sharply (one +80%, one -40%)",
        "price_overrides": {"AMSC": 91.00, "PBR": 12.05},
    },
    "crash": {
        "description": "Broad selloff: all positions drop 15-25%",
        "price_overrides": {
            "AMSC": 40.42, "VZ": 39.51, "PLAB": 32.56, "CMCSA": 22.39,
            "CNH": 8.50, "PBR": 16.06, "CODA": 9.23,
        },
    },
    "moonshot": {
        "description": "One position 5x (simulates breakout)",
        "price_overrides": {"PLAB": 203.50},
    },
}


def run_synthetic(config: BotConfig, scenario_name: str) -> SimQuarterResult:
    """Inject synthetic prices and run one rebalance cycle."""
    scenario = SYNTHETIC_SCENARIOS[scenario_name]
    total_portfolio = 1000.0
    cash = total_portfolio * config.target_weights.get("CASH", 0.107)
    shares = compute_initial_shares(config, total_portfolio)

    # Start from entry prices, then apply overrides
    prices = dict(ENTRY_PRICES)
    prices.update(scenario["price_overrides"])

    snapshot = build_snapshot_from_prices(prices, shares, cash)
    result = calculate_drift(snapshot, config)

    messages = []
    if result.needs_rebalance:
        messages.append(format_rebalance_message(result))
        messages.append(format_trade_confirmation(result.trades, dry_run=True))

    return SimQuarterResult(
        date="SYNTHETIC",
        driver=f"{scenario_name}: {scenario['description']}",
        portfolio_value=snapshot.total_value,
        cash=cash,
        max_drift=result.max_drift,
        needs_rebalance=result.needs_rebalance,
        trades=result.trades,
        messages=messages,
    )


# --- Guardrail Stress Tests ---

@dataclass
class StressTestResult:
    name: str
    passed: bool
    detail: str


def run_stress_tests(config: BotConfig) -> list[StressTestResult]:
    """Run all guardrail stress tests."""
    results: list[StressTestResult] = []

    # Test 1: Daily loss limit kill switch at -3%
    executor = OrderExecutor(config)
    triggered = executor.check_daily_loss_limit(start_value=10000, current_value=9650)
    results.append(StressTestResult(
        "Kill switch: -3.5% daily loss",
        triggered,
        "Kill switch correctly triggered" if triggered else "FAIL: kill switch did not trigger",
    ))

    not_triggered = executor.check_daily_loss_limit(start_value=10000, current_value=9800)
    results.append(StressTestResult(
        "Kill switch: -2.0% daily loss (should NOT trigger)",
        not not_triggered,
        "Correctly ignored" if not not_triggered else "FAIL: false trigger at -2%",
    ))

    # Test 2: Position size cap (>15% of portfolio)
    total = 1000.0
    cash = total * config.target_weights.get("CASH", 0.126)
    shares = compute_initial_shares(config, total)
    # Make PLAB massively overweight by inflating its price
    prices = dict(ENTRY_PRICES)
    prices["PLAB"] = 400.00
    snapshot = build_snapshot_from_prices(prices, shares, cash)
    result = calculate_drift(snapshot, config)
    # Check that no single trade exceeds 15% of portfolio
    max_trade_pct = max(
        (t.estimated_value / snapshot.total_value for t in result.trades),
        default=0,
    )
    capped = max_trade_pct <= config.max_position_pct + 0.001  # small float tolerance
    results.append(StressTestResult(
        "Position cap: single order <= 15% of portfolio",
        capped,
        f"Max trade: {max_trade_pct:.1%} of portfolio"
        + (" (correctly capped)" if capped else " FAIL: exceeded cap"),
    ))

    # Test 3: Zero/empty portfolio handling
    empty_snapshot = PortfolioSnapshot(positions={}, total_value=0, cash=0, timestamp="TEST")
    empty_result = calculate_drift(empty_snapshot, config)
    results.append(StressTestResult(
        "Empty portfolio: no crash on $0 portfolio",
        not empty_result.needs_rebalance and empty_result.max_drift == 0,
        "Handled gracefully" if not empty_result.needs_rebalance else "FAIL: unexpected behavior",
    ))

    # Test 4: Missing ticker (position exists in config but not in snapshot)
    partial_prices = {"VZ": 49.39, "AMSC": 50.52}  # only 2 of 7
    partial_shares = {"VZ": 2.0, "AMSC": 3.0}
    partial_snap = build_snapshot_from_prices(partial_prices, partial_shares, 500)
    partial_result = calculate_drift(partial_snap, config)
    results.append(StressTestResult(
        "Missing tickers: 5 of 7 positions absent",
        partial_result.needs_rebalance,
        f"Drift: {partial_result.max_drift:.1%}, trades: {len(partial_result.trades)}"
        + " (correctly detected massive drift)",
    ))

    # Test 5: Kill switch message formatting
    msg = format_kill_switch_alert(0.035)
    results.append(StressTestResult(
        "Kill switch alert formatting",
        "KILL SWITCH" in msg and "3.5%" in msg,
        "Message formatted correctly" if "KILL SWITCH" in msg else "FAIL: bad format",
    ))

    # Test 6: Trade logging to SQLite
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        trade_logger = TradeLogger(db_path)
        test_trade = Trade("TEST", "BUY", 10, 500.0, "stress test")
        trade_logger.log_trade(test_trade, "SIM_TEST", dry_run=True)
        recent = trade_logger.get_recent_trades(1)
        logged_ok = len(recent) == 1 and recent[0]["ticker"] == "TEST"
        results.append(StressTestResult(
            "SQLite trade logging",
            logged_ok,
            "Trade logged and retrieved" if logged_ok else "FAIL: logging broken",
        ))
    finally:
        os.unlink(db_path)

    # Test 7: Rebalance message formatting (no crash on empty trades)
    no_trade_result = RebalanceResult(
        max_drift=0.02, needs_rebalance=False, trades=[], drifts={"VZ": 0.02},
    )
    msg = format_rebalance_message(no_trade_result)
    results.append(StressTestResult(
        "Message format: empty trade list",
        "Rebalance Proposal" in msg,
        "Formatted without crash",
    ))

    # Test 8: Extreme drift (one position = 90% of portfolio)
    extreme_prices = dict(ENTRY_PRICES)
    extreme_prices["AMSC"] = 5000.00  # absurd price
    extreme_snap = build_snapshot_from_prices(extreme_prices, shares, cash)
    extreme_result = calculate_drift(extreme_snap, config)
    results.append(StressTestResult(
        "Extreme drift: one position ~90% of portfolio",
        extreme_result.needs_rebalance and len(extreme_result.trades) > 0,
        f"Max drift: {extreme_result.max_drift:.1%}, {len(extreme_result.trades)} trades generated",
    ))

    return results


# --- CLI ---

def print_historical_replay(results: list[SimQuarterResult]) -> None:
    """Print formatted historical replay results."""
    print(f"\n{'='*70}")
    print("  BOT SIMULATION — Historical Replay (Oct 2024 → Apr 2026)")
    print(f"{'='*70}")
    print()

    summary_rows = []
    rebalance_count = 0
    total_trades = 0

    for r in results:
        rebal = "YES" if r.needs_rebalance else "no"
        if r.needs_rebalance:
            rebalance_count += 1
            total_trades += len(r.trades)
        summary_rows.append([
            r.date,
            f"€{r.portfolio_value:,.0f}",
            f"{r.max_drift:.1%}",
            rebal,
            len(r.trades),
            r.driver,
        ])

    print(tabulate(
        summary_rows,
        headers=["Quarter", "Value", "Max Drift", "Rebal?", "Trades", "Driver"],
        tablefmt="simple",
    ))

    print(f"\n  Rebalance events: {rebalance_count} of {len(results)} quarters")
    print(f"  Total trades generated: {total_trades}")

    # Show details for quarters that triggered rebalancing
    for r in results:
        if not r.needs_rebalance:
            continue
        print(f"\n  --- {r.date}: {r.driver} ---")
        for trade in r.trades:
            emoji = "BUY " if trade.action == "BUY" else "SELL"
            print(f"    {emoji} {trade.shares:>3d} {trade.ticker:<6s} "
                  f"(~${trade.estimated_value:>7,.0f})  {trade.reason}")
        print()
        # Show what the Telegram message would look like
        if r.messages:
            print("  Telegram message preview:")
            print("  " + "\n  ".join(r.messages[0].split("\n")[:8]))
            print("  ...")
            print()


def print_synthetic_result(result: SimQuarterResult, scenario_name: str) -> None:
    """Print a single synthetic scenario result."""
    print(f"\n  Scenario: {scenario_name}")
    print(f"  {result.driver}")
    print(f"  Portfolio: ${result.portfolio_value:,.0f} | Max drift: {result.max_drift:.1%}")
    print(f"  Needs rebalance: {result.needs_rebalance} | Trades: {len(result.trades)}")

    if result.trades:
        for trade in result.trades:
            print(f"    {trade.action} {trade.shares} {trade.ticker} "
                  f"(~${trade.estimated_value:,.0f}) — {trade.reason}")


def print_stress_results(results: list[StressTestResult]) -> None:
    """Print stress test results."""
    print(f"\n{'='*70}")
    print("  GUARDRAIL STRESS TESTS")
    print(f"{'='*70}")
    print()

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    rows = []
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        rows.append([status, r.name, r.detail])

    print(tabulate(rows, headers=["Status", "Test", "Detail"], tablefmt="simple"))
    print(f"\n  Result: {passed}/{total} passed", end="")
    if passed == total:
        print(" — all guardrails verified")
    else:
        print(f" — {total - passed} FAILURES need attention")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="VCI Bot Simulator")
    parser.add_argument(
        "--stress", action="store_true",
        help="Run guardrail stress tests",
    )
    parser.add_argument(
        "--synthetic", choices=list(SYNTHETIC_SCENARIOS.keys()),
        help="Run a synthetic drift scenario",
    )
    parser.add_argument(
        "--all-synthetic", action="store_true",
        help="Run all synthetic drift scenarios",
    )
    args = parser.parse_args()

    # Use a temp DB so we don't pollute real data
    config = BotConfig(dry_run=True, db_path=":memory:")

    if args.stress:
        results = run_stress_tests(config)
        print_stress_results(results)
        return

    if args.synthetic:
        print(f"\n{'='*70}")
        print("  SYNTHETIC DRIFT INJECTION")
        print(f"{'='*70}")
        result = run_synthetic(config, args.synthetic)
        print_synthetic_result(result, args.synthetic)
        print()
        return

    if args.all_synthetic:
        print(f"\n{'='*70}")
        print("  SYNTHETIC DRIFT INJECTION — All Scenarios")
        print(f"{'='*70}")
        for name in SYNTHETIC_SCENARIOS:
            result = run_synthetic(config, name)
            print_synthetic_result(result, name)
        print()
        return

    # Default: historical replay
    results = replay_historical(config)
    print_historical_replay(results)

    # Also run stress tests
    stress_results = run_stress_tests(config)
    print_stress_results(stress_results)

    # Also run all synthetic scenarios
    print(f"\n{'='*70}")
    print("  SYNTHETIC DRIFT SCENARIOS")
    print(f"{'='*70}")
    for name in SYNTHETIC_SCENARIOS:
        result = run_synthetic(config, name)
        print_synthetic_result(result, name)
    print()


if __name__ == "__main__":
    main()
