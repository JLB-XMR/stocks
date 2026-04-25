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
import os
import sys

from tabulate import tabulate

from backtest.benchmarks import (
    INDEX_DATA,
    VCI_AS_INDEX,
    compare_to_all_indexes,
    portfolio_to_index_quarters,
)
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


def cmd_backtest_bench(_args: argparse.Namespace) -> None:
    bt = get_vci_backtest()
    comparisons = compare_to_all_indexes(VCI_AS_INDEX)

    print(f"\n{'='*80}")
    print("  VCI Portfolio vs Market Indexes (Oct 2024 → Apr 2026)")
    print(f"{'='*80}")
    print()

    # Summary table
    rows = []
    for c in comparisons:
        rows.append([
            c.index_name,
            c.index_ticker,
            f"{c.portfolio_total_return:+.1f}%",
            f"{c.index_total_return:+.1f}%",
            f"{c.alpha:+.1f}pp",
            f"{c.portfolio_max_drawdown:.1f}%",
            f"{c.index_max_drawdown:.1f}%",
            f"{c.portfolio_sharpe:.2f}",
            f"{c.index_sharpe:.2f}",
            f"{c.beta:.2f}",
        ])

    print(tabulate(
        rows,
        headers=["Index", "Ticker", "VCI Ret", "Idx Ret", "Alpha",
                 "VCI MDD", "Idx MDD", "VCI Shrp", "Idx Shrp", "Beta"],
        tablefmt="simple",
    ))
    print()

    # Detailed metrics
    print("  Detailed Risk Metrics:")
    detail_rows = []
    for c in comparisons:
        detail_rows.append([
            c.index_name,
            f"{c.portfolio_volatility:.1%}",
            f"{c.index_volatility:.1%}",
            f"{c.correlation:.2f}",
            f"{c.tracking_error:.1%}",
            f"{c.information_ratio:.2f}",
        ])

    print(tabulate(
        detail_rows,
        headers=["Index", "VCI Vol", "Idx Vol", "Corr", "Track Err", "Info Ratio"],
        tablefmt="simple",
    ))
    print()

    # Quarterly side-by-side with S&P 500
    sp500 = INDEX_DATA["S&P 500"]
    print("  Quarterly: VCI vs S&P 500:")
    q_rows = []
    for i, q in enumerate(bt.quarters):
        idx_q = sp500[i]
        spread = q.qoq_change - idx_q.qoq_return
        q_rows.append([
            q.date,
            f"€{q.portfolio_value:,.0f}",
            f"{q.qoq_change:+.1f}%",
            f"{idx_q.value:,.0f}",
            f"{idx_q.qoq_return:+.1f}%",
            f"{spread:+.1f}pp",
            q.key_driver,
        ])

    print(tabulate(
        q_rows,
        headers=["Quarter", "VCI", "VCI QoQ", "S&P", "S&P QoQ", "Spread", "Driver"],
        tablefmt="simple",
    ))

    # Key takeaways
    sp_comp = next(c for c in comparisons if c.index_name == "S&P 500")
    bond_comp = next(c for c in comparisons if "Bond" in c.index_name)
    print()
    print("  Key Takeaways:")
    print(f"    vs S&P 500:  {sp_comp.alpha:+.1f}pp alpha, "
          f"{sp_comp.portfolio_max_drawdown:.1f}% vs {sp_comp.index_max_drawdown:.1f}% MDD")
    if sp_comp.portfolio_sharpe > sp_comp.index_sharpe:
        print(f"    Sharpe:      VCI ({sp_comp.portfolio_sharpe:.2f}) > S&P ({sp_comp.index_sharpe:.2f}) "
              f"— better risk-adjusted returns")
    else:
        print(f"    Sharpe:      VCI ({sp_comp.portfolio_sharpe:.2f}) < S&P ({sp_comp.index_sharpe:.2f}) "
              f"— worse risk-adjusted returns")
    if bond_comp.portfolio_sharpe > bond_comp.index_sharpe:
        print(f"    vs Bonds:    Equity risk compensated "
              f"(VCI Sharpe {bond_comp.portfolio_sharpe:.2f} > AGG {bond_comp.index_sharpe:.2f})")
    else:
        print(f"    vs Bonds:    Equity risk NOT compensated "
              f"(VCI Sharpe {bond_comp.portfolio_sharpe:.2f} < AGG {bond_comp.index_sharpe:.2f})")
    print(f"    Beta:        {sp_comp.beta:.2f} (< 1 = less volatile than S&P)")
    print(f"    Correlation: {sp_comp.correlation:.2f} to S&P 500")
    print()


def cmd_dashboard(args: argparse.Namespace) -> None:
    from dashboard.sheets import create_dashboard

    credentials = args.credentials
    if not credentials:
        credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")

    try:
        url = create_dashboard(
            credentials_path=credentials,
            sheet_id=args.update,
            share_email=args.share,
        )
        print(f"\nDashboard URL: {url}")
    except FileNotFoundError:
        print(f"\nCredentials file not found: {credentials}")
        print("To set up Google Sheets:")
        print("  1. Create a Google Cloud project, enable Sheets API")
        print("  2. Create a service account, download JSON key")
        print("  3. Run: python analyze.py dashboard --credentials /path/to/key.json --share you@email.com")
    except RuntimeError as e:
        print(f"\n{e}")


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


def cmd_reallocate(_args: argparse.Namespace) -> None:
    from rebalance.vci_reallocate import run_reallocation
    print(run_reallocation())


def cmd_compare(_args: argparse.Namespace) -> None:
    from backtest.comparison import compare_portfolios, run_ibkr_benchmark
    print(compare_portfolios())
    print(run_ibkr_benchmark())


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

    # backtest-bench
    p_bench = subparsers.add_parser("backtest-bench", help="Backtest with index benchmarks")
    p_bench.set_defaults(func=cmd_backtest_bench)

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Create/update Google Sheets dashboard")
    p_dash.add_argument("--update", metavar="SHEET_ID", help="Update existing spreadsheet")
    p_dash.add_argument("--share", metavar="EMAIL", help="Email to share with")
    p_dash.add_argument("--credentials", help="Path to service account JSON key")
    p_dash.set_defaults(func=cmd_dashboard)

    # simulate
    p_sim = subparsers.add_parser("simulate", help="Run bot simulation & stress tests")
    p_sim.add_argument(
        "mode", nargs="?", default="all",
        choices=["all", "stress", "synthetic"],
        help="Simulation mode (default: all)",
    )
    p_sim.set_defaults(func=cmd_simulate)

    # reallocate
    p_realloc = subparsers.add_parser("reallocate", help="VCI reallocation plan for IBKR portfolio")
    p_realloc.set_defaults(func=cmd_reallocate)

    # compare
    p_compare = subparsers.add_parser("compare", help="Compare thesis vs actual IBKR portfolio")
    p_compare.set_defaults(func=cmd_compare)

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
