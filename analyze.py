#!/usr/bin/env python3
"""Investment Portfolio Analysis CLI.

Usage:
    python analyze.py portfolio vci      Show VCI portfolio summary
    python analyze.py portfolio moonshot Show Moonshot portfolio summary
    python analyze.py backtest           Show VCI 18-month backtest
    python analyze.py scenarios          Show Moonshot return scenarios
    python analyze.py dca                Run DCA decision tree (interactive)
    python analyze.py rebalance          Run quarterly rebalance checks
    python analyze.py risk <TICKER>      Show geopolitical risk for a stock
    python analyze.py universe           Show all stocks in the universe
"""

import argparse
import sys

from tabulate import tabulate

from backtest.engine import calculate_scenario_returns, get_vci_backtest
from data.models import GeopoliticalRisk
from data.stocks import UNIVERSE
from portfolios.moonshot import RETURN_ETAS, RETURN_SCENARIOS, build_moonshot_portfolio
from portfolios.vci import build_vci_portfolio
from bot.config import BotConfig
from rebalance.dca import DCA_NEVER_RULES, decide_monthly_addition
from risk.stress_test import (
    GEOPOLITICAL_ASSESSMENTS,
    IMMEDIATE_CUT_TRIGGERS,
    NEVER_CUT_TRIGGERS,
    POLITICAL_CALENDAR,
    QUARTERLY_REVIEW_CUT_TRIGGERS,
    the_one_rule,
)


def cmd_portfolio(args: argparse.Namespace) -> None:
    if args.name == "vci":
        p = build_vci_portfolio()
    elif args.name == "moonshot":
        p = build_moonshot_portfolio()
    else:
        print(f"Unknown portfolio: {args.name}")
        return

    print(f"\n{'='*60}")
    print(f"  {p.name}")
    print(f"{'='*60}")
    print(f"  {p.description}")
    print(f"  Currency: {p.currency} | Total: ${p.total_value:,.0f}")
    print(f"  Cash: ${p.cash:,.0f}")
    print()

    rows = []
    for pos in p.positions:
        rows.append([
            pos.tier.value,
            pos.stock.ticker,
            pos.stock.name,
            f"{pos.shares:.1f}" if pos.shares else "—",
            f"${pos.entry_price:.2f}",
            f"${pos.stock.price:.2f}" if pos.stock.price else "—",
            f"{pos.stock.ttm_pe:.1f}x" if pos.stock.ttm_pe else "Loss",
            pos.stock.debt_level.value,
            f"{pos.weight:.1%}",
        ])

    print(tabulate(
        rows,
        headers=["Tier", "Ticker", "Name", "Shares", "Entry", "Current", "P/E", "Debt", "Weight"],
        tablefmt="simple",
    ))
    print()


def cmd_backtest(_args: argparse.Namespace) -> None:
    bt = get_vci_backtest()

    print(f"\n{'='*60}")
    print("  VCI Portfolio — 18-Month Backtest (Oct 2024 → Apr 2026)")
    print(f"{'='*60}")
    print()

    summary = [
        ["Total return", f"+{bt.total_return:.1f}%"],
        ["S&P 500 return", f"{bt.benchmark_return:.1f}%"],
        ["Alpha", f"+{bt.total_return - bt.benchmark_return:.1f} pp"],
        ["Peak value", f"€{bt.peak_value:,.0f}"],
        ["Trough value", f"€{bt.trough_value:,.0f}"],
        ["Max drawdown", f"{bt.max_drawdown:.1f}%"],
    ]
    print(tabulate(summary, tablefmt="simple"))
    print()

    print("Quarterly Timeline:")
    q_rows = [[q.date, f"€{q.portfolio_value:,.0f}", f"{q.qoq_change:+.1f}%", q.key_driver]
              for q in bt.quarters]
    print(tabulate(q_rows, headers=["Date", "Value", "QoQ", "Driver"], tablefmt="simple"))
    print()

    print("Winners:")
    for ticker, ret in sorted(bt.winners.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ticker}: +{ret:.1f}%")

    print("\nDetractors:")
    for ticker, ret in sorted(bt.detractors.items(), key=lambda x: x[1]):
        print(f"  {ticker}: {ret:.1f}%")
    print()


def cmd_scenarios(_args: argparse.Namespace) -> None:
    p = build_moonshot_portfolio()
    cost_bases = {pos.stock.ticker: pos.cost_basis for pos in p.positions}

    print(f"\n{'='*60}")
    print("  Moonshot Portfolio — Return Scenarios")
    print(f"{'='*60}")
    print()

    for scenario in RETURN_SCENARIOS:
        calculated = calculate_scenario_returns(cost_bases, p.cash, scenario.multipliers)
        rows = [[t, f"{m}x"] for t, m in scenario.multipliers.items()]
        rows.append(["PORTFOLIO", f"~{calculated:.0f}x (documented: ~{scenario.portfolio_multiple:.0f}x)"])
        print(f"  {scenario.name} Case:")
        print(tabulate(rows, headers=["Ticker", "Multiple"], tablefmt="simple"))
        print()

    print("  Return ETAs:")
    for ticker, info in RETURN_ETAS.items():
        print(f"    {ticker}: {info['eta']} — {info['trigger']}")
    print()


def cmd_dca(_args: argparse.Namespace) -> None:
    p = build_moonshot_portfolio()

    print(f"\n{'='*60}")
    print("  DCA Decision Tree (Monthly €200-300)")
    print(f"{'='*60}")
    print()

    # Example: run with default conditions
    decision = decide_monthly_addition(
        portfolio=p,
        monthly_amount=250.0,
    )

    print(f"  Action:  {decision.action}")
    print(f"  Ticker:  {decision.ticker or 'N/A'}")
    print(f"  Amount:  ${decision.amount:.0f}")
    print(f"  Reason:  {decision.reason}")
    print()

    print("  NEVER do with monthly additions:")
    for rule in DCA_NEVER_RULES:
        print(f"    ✗ {rule}")
    print()

    print("  The One Rule:")
    print('    "If I didn\'t own this and had fresh cash today, would I buy at this price?"')
    print(f"    YES → {the_one_rule(True)}")
    print(f"    NO  → {the_one_rule(False)}")
    print()


def cmd_risk(args: argparse.Namespace) -> None:
    ticker = args.ticker.upper() if args.ticker else None

    print(f"\n{'='*60}")
    print("  Geopolitical Stress Test & Risk Assessment")
    print(f"{'='*60}")
    print()

    if ticker:
        assessment = next((a for a in GEOPOLITICAL_ASSESSMENTS if a.ticker == ticker), None)
        stock = UNIVERSE.get(ticker)

        if assessment:
            print(f"  {ticker} — {assessment.risk_level.value} risk")
            print(f"  Impact: {assessment.impact}")
            print(f"  Action: {assessment.action}")
            print(f"  Net beneficiary: {'Yes' if assessment.is_net_beneficiary else 'No'}")
        elif stock:
            print(f"  {ticker} — {stock.geopolitical_risk.value} risk")
            print(f"  No detailed assessment available.")
        else:
            print(f"  {ticker} not found in universe.")
        print()
        return

    # Show all assessments
    rows = [[a.ticker, a.risk_level.value, a.impact, a.action]
            for a in GEOPOLITICAL_ASSESSMENTS]
    print(tabulate(rows, headers=["Ticker", "Risk", "Impact", "Action"], tablefmt="simple"))
    print()

    print("  Political Calendar:")
    for event in POLITICAL_CALENDAR:
        print(f"\n  {event['event']} ({event['date']}):")
        for impact in event["impact"]:
            print(f"    • {impact}")

    print(f"\n\n  Loss-Cutting Rules:")
    print("\n  CUT IMMEDIATELY:")
    for trigger in IMMEDIATE_CUT_TRIGGERS:
        print(f"    🔴 {trigger}")
    print("\n  CUT AFTER QUARTERLY REVIEW:")
    for trigger in QUARTERLY_REVIEW_CUT_TRIGGERS:
        print(f"    🟡 {trigger}")
    print("\n  NEVER CUT BECAUSE:")
    for trigger in NEVER_CUT_TRIGGERS:
        print(f"    🟢 {trigger}")
    print()


def cmd_simulate(args: argparse.Namespace) -> None:
    from bot.simulator import (
        SYNTHETIC_SCENARIOS,
        print_historical_replay,
        print_stress_results,
        print_synthetic_result,
        replay_historical,
        run_stress_tests,
        run_synthetic,
    )

    config = BotConfig(dry_run=True, db_path=":memory:")

    if args.mode == "stress":
        results = run_stress_tests(config)
        print_stress_results(results)
    elif args.mode == "synthetic":
        print(f"\n{'='*60}")
        print("  SYNTHETIC DRIFT — All Scenarios")
        print(f"{'='*60}")
        for name in SYNTHETIC_SCENARIOS:
            result = run_synthetic(config, name)
            print_synthetic_result(result, name)
        print()
    else:  # "all" or default
        results = replay_historical(config)
        print_historical_replay(results)
        stress = run_stress_tests(config)
        print_stress_results(stress)


def cmd_universe(_args: argparse.Namespace) -> None:
    print(f"\n{'='*60}")
    print("  Stock Universe — All Discussed (Apr 2-4, 2026)")
    print(f"{'='*60}")
    print()

    rows = []
    for ticker, s in sorted(UNIVERSE.items()):
        rows.append([
            s.ticker,
            s.name,
            s.sector.value,
            f"${s.price:.2f}" if s.price else "—",
            f"${s.market_cap_millions:,.0f}M",
            f"{s.ttm_pe:.1f}x" if s.ttm_pe else "Loss/Trough",
            s.geopolitical_risk.value,
            s.debt_level.value,
        ])

    print(tabulate(
        rows,
        headers=["Ticker", "Name", "Sector", "Price", "MC", "P/E", "Geo Risk", "Debt"],
        tablefmt="simple",
    ))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Investment Portfolio Analysis — April 2026",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # portfolio
    p_port = subparsers.add_parser("portfolio", help="Show portfolio summary")
    p_port.add_argument("name", choices=["vci", "moonshot"], help="Portfolio name")
    p_port.set_defaults(func=cmd_portfolio)

    # backtest
    p_bt = subparsers.add_parser("backtest", help="Show VCI backtest results")
    p_bt.set_defaults(func=cmd_backtest)

    # scenarios
    p_sc = subparsers.add_parser("scenarios", help="Show moonshot return scenarios")
    p_sc.set_defaults(func=cmd_scenarios)

    # dca
    p_dca = subparsers.add_parser("dca", help="Run DCA decision tree")
    p_dca.set_defaults(func=cmd_dca)

    # rebalance (alias for quarterly)
    p_reb = subparsers.add_parser("rebalance", help="Run quarterly rebalance checks")
    p_reb.set_defaults(func=cmd_dca)  # shares output for now

    # risk
    p_risk = subparsers.add_parser("risk", help="Geopolitical risk assessment")
    p_risk.add_argument("ticker", nargs="?", help="Stock ticker (optional)")
    p_risk.set_defaults(func=cmd_risk)

    # simulate
    p_sim = subparsers.add_parser("simulate", help="Run bot simulation & stress tests")
    p_sim.add_argument(
        "mode", nargs="?", default="all",
        choices=["all", "stress", "synthetic"],
        help="Simulation mode (default: all)",
    )
    p_sim.set_defaults(func=cmd_simulate)

    # universe
    p_uni = subparsers.add_parser("universe", help="Show all stocks")
    p_uni.set_defaults(func=cmd_universe)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
