"""Google Sheets dashboard integration.

Exports portfolio data, backtest results, benchmark comparisons, and risk
assessments to Google Sheets for a live dashboard.

Authentication: uses a service account JSON key file.
Set GOOGLE_SHEETS_CREDENTIALS in .env to the path of the key file.

Usage:
    python -m dashboard.sheets                     # Create new dashboard
    python -m dashboard.sheets --update SHEET_ID   # Update existing
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Column widths for formatting
COL_NARROW = 80
COL_MEDIUM = 120
COL_WIDE = 200


def _get_sheets_client(credentials_path: str):
    """Authenticate and return a gspread client."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        raise RuntimeError(
            "Required packages missing. Install with:\n"
            "  pip install gspread google-auth"
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
    return gspread.authorize(creds)


def _safe_val(v) -> str | float:
    """Convert value for Sheets (handle None, enums, etc.)."""
    if v is None:
        return ""
    if hasattr(v, "value"):  # Enum
        return v.value
    return v


def create_dashboard(
    credentials_path: str,
    sheet_id: str | None = None,
    share_email: str | None = None,
) -> str:
    """Create or update a Google Sheets dashboard with all portfolio data.

    Args:
        credentials_path: Path to Google service account JSON key
        sheet_id: Existing spreadsheet ID to update (creates new if None)
        share_email: Email to share the sheet with (optional)

    Returns:
        Spreadsheet URL
    """
    from backtest.benchmarks import (
        INDEX_DATA,
        VCI_AS_INDEX,
        compare_to_all_indexes,
        portfolio_to_index_quarters,
    )
    from backtest.engine import get_vci_backtest
    from data.stocks import UNIVERSE
    from portfolios.moonshot import RETURN_ETAS, RETURN_SCENARIOS, build_moonshot_portfolio
    from portfolios.vci import build_vci_portfolio
    from risk.stress_test import (
        GEOPOLITICAL_ASSESSMENTS,
        IMMEDIATE_CUT_TRIGGERS,
        NEVER_CUT_TRIGGERS,
        POLITICAL_CALENDAR,
        QUARTERLY_REVIEW_CUT_TRIGGERS,
    )

    gc = _get_sheets_client(credentials_path)

    if sheet_id:
        spreadsheet = gc.open_by_key(sheet_id)
        logger.info("Updating existing spreadsheet: %s", sheet_id)
    else:
        title = f"VCI Portfolio Dashboard — {datetime.now().strftime('%Y-%m-%d')}"
        spreadsheet = gc.create(title)
        logger.info("Created new spreadsheet: %s", spreadsheet.url)

    if share_email:
        spreadsheet.share(share_email, perm_type="user", role="writer")
        logger.info("Shared with %s", share_email)

    # --- Sheet 1: Portfolio Overview ---
    _write_portfolio_overview(spreadsheet, build_vci_portfolio(), build_moonshot_portfolio())

    # --- Sheet 2: Benchmark Comparison ---
    _write_benchmark_sheet(spreadsheet, VCI_AS_INDEX)

    # --- Sheet 3: Quarterly Performance ---
    _write_quarterly_sheet(spreadsheet, get_vci_backtest(), VCI_AS_INDEX)

    # --- Sheet 4: Risk Dashboard ---
    _write_risk_sheet(spreadsheet)

    # --- Sheet 5: Moonshot Scenarios ---
    _write_moonshot_sheet(spreadsheet, build_moonshot_portfolio())

    # --- Sheet 6: Stock Universe ---
    _write_universe_sheet(spreadsheet)

    # Remove default Sheet1 if we created new sheets
    try:
        default = spreadsheet.worksheet("Sheet1")
        spreadsheet.del_worksheet(default)
    except Exception:
        pass

    return spreadsheet.url


def _get_or_create_worksheet(spreadsheet, title: str, rows: int = 100, cols: int = 20):
    """Get existing worksheet or create new one."""
    try:
        ws = spreadsheet.worksheet(title)
        ws.clear()
        return ws
    except Exception:
        return spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)


def _write_portfolio_overview(spreadsheet, vci, moonshot):
    """Sheet 1: Both portfolios side by side."""
    ws = _get_or_create_worksheet(spreadsheet, "Portfolio Overview")

    rows = [
        ["PORTFOLIO OVERVIEW", "", "", "", "", "", "", "", "",
         f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
        [],
        ["=== VCI (Value Convergence Index) ==="],
        [vci.description],
        [f"Total: {vci.currency} {vci.total_value:,.0f}", "", f"Cash: {vci.currency} {vci.cash:,.0f}"],
        [],
        ["Tier", "Ticker", "Name", "Shares", "Entry", "Current", "P/E",
         "Debt", "Weight", "Return"],
    ]

    for pos in vci.positions:
        ret = ((pos.stock.price / pos.entry_price) - 1) * 100 if pos.entry_price and pos.stock.price else 0
        rows.append([
            pos.tier.value, pos.stock.ticker, pos.stock.name,
            round(pos.shares, 1), pos.entry_price,
            pos.stock.price or "", f"{pos.stock.ttm_pe:.1f}x" if pos.stock.ttm_pe else "Loss",
            pos.stock.debt_level.value, f"{pos.weight:.1%}", f"{ret:+.1f}%",
        ])

    rows.extend([
        [],
        ["=== MOONSHOT ($1,500) ==="],
        [moonshot.description],
        [f"Total: {moonshot.currency} {moonshot.total_value:,.0f}", "",
         f"Cash: {moonshot.currency} {moonshot.cash:,.0f}"],
        [],
        ["Tier", "Ticker", "Name", "Shares", "Entry", "Current", "P/E",
         "Debt", "Weight", "Cost Basis"],
    ])

    for pos in moonshot.positions:
        rows.append([
            pos.tier.value, pos.stock.ticker, pos.stock.name,
            pos.shares, pos.entry_price,
            pos.stock.price or "", f"{pos.stock.ttm_pe:.1f}x" if pos.stock.ttm_pe else "Loss",
            pos.stock.debt_level.value, f"{pos.weight:.1%}", f"${pos.cost_basis:,.0f}",
        ])

    ws.update(range_name="A1", values=rows)


def _write_benchmark_sheet(spreadsheet, vci_quarters):
    """Sheet 2: Benchmark comparison against all indexes."""
    from backtest.benchmarks import compare_to_all_indexes

    ws = _get_or_create_worksheet(spreadsheet, "Benchmark Comparison")
    comparisons = compare_to_all_indexes(vci_quarters)

    rows = [
        ["VCI vs MARKET INDEXES", "", "", "", "", "", "", "", "", "", "", ""],
        ["Period: Oct 2024 - Apr 2026 (18 months)"],
        [],
        ["Index", "Ticker", "VCI Return", "Index Return", "Alpha",
         "VCI MaxDD", "Idx MaxDD", "VCI Vol", "Idx Vol",
         "VCI Sharpe", "Idx Sharpe", "Correlation", "Beta"],
    ]

    for c in comparisons:
        rows.append([
            c.index_name, c.index_ticker,
            f"{c.portfolio_total_return:+.1f}%", f"{c.index_total_return:+.1f}%",
            f"{c.alpha:+.1f}pp",
            f"{c.portfolio_max_drawdown:.1f}%", f"{c.index_max_drawdown:.1f}%",
            f"{c.portfolio_volatility:.1%}", f"{c.index_volatility:.1%}",
            f"{c.portfolio_sharpe:.2f}", f"{c.index_sharpe:.2f}",
            f"{c.correlation:.2f}", f"{c.beta:.2f}",
        ])

    rows.extend([
        [],
        ["INTERPRETATION"],
        ["Alpha > 0: VCI outperformed the index"],
        ["Sharpe > index Sharpe: better risk-adjusted returns"],
        ["Beta < 1: less volatile than index; Beta > 1: more volatile"],
        ["Correlation close to 0: good diversification benefit"],
        [],
        ["Risk-free rate assumption: 4.5% annualized (T-bill, Apr 2026)"],
    ])

    ws.update(range_name="A1", values=rows)


def _write_quarterly_sheet(spreadsheet, backtest, vci_quarters):
    """Sheet 3: Quarter-by-quarter with index overlays."""
    from backtest.benchmarks import INDEX_DATA

    ws = _get_or_create_worksheet(spreadsheet, "Quarterly Performance")

    # Header row with all indexes
    header = ["Quarter", "VCI Value", "VCI QoQ", "Driver"]
    index_names = list(INDEX_DATA.keys())
    for name in index_names:
        header.extend([f"{name} Value", f"{name} QoQ"])

    rows = [
        ["QUARTERLY PERFORMANCE — VCI vs ALL INDEXES"],
        [],
        header,
    ]

    for i, q in enumerate(backtest.quarters):
        row = [q.date, f"{q.portfolio_value:,.0f}", f"{q.qoq_change:+.1f}%", q.key_driver]
        for name in index_names:
            idx_q = INDEX_DATA[name][i]
            row.extend([f"{idx_q.value:,.0f}", f"{idx_q.qoq_return:+.1f}%"])
        rows.append(row)

    rows.extend([
        [],
        ["ATTRIBUTION"],
        ["Winners:"],
    ])
    for t, r in sorted(backtest.winners.items(), key=lambda x: x[1], reverse=True):
        rows.append(["", t, f"+{r:.1f}%"])
    rows.append(["Detractors:"])
    for t, r in sorted(backtest.detractors.items(), key=lambda x: x[1]):
        rows.append(["", t, f"{r:.1f}%"])

    ws.update(range_name="A1", values=rows)


def _write_risk_sheet(spreadsheet):
    """Sheet 4: Risk dashboard."""
    from risk.stress_test import (
        GEOPOLITICAL_ASSESSMENTS,
        IMMEDIATE_CUT_TRIGGERS,
        NEVER_CUT_TRIGGERS,
        POLITICAL_CALENDAR,
        QUARTERLY_REVIEW_CUT_TRIGGERS,
    )

    ws = _get_or_create_worksheet(spreadsheet, "Risk Dashboard")

    rows = [
        ["RISK DASHBOARD"],
        [],
        ["GEOPOLITICAL RISK ASSESSMENT"],
        ["Ticker", "Risk Level", "Impact", "Action", "Net Beneficiary"],
    ]
    for a in GEOPOLITICAL_ASSESSMENTS:
        rows.append([a.ticker, a.risk_level.value, a.impact, a.action,
                      "Yes" if a.is_net_beneficiary else "No"])

    rows.extend([[], ["POLITICAL CALENDAR"]])
    for event in POLITICAL_CALENDAR:
        rows.append([event["event"], event["date"]])
        for impact in event["impact"]:
            rows.append(["", impact])

    rows.extend([[], ["LOSS-CUTTING RULES"]])
    rows.append(["CUT IMMEDIATELY:"])
    for t in IMMEDIATE_CUT_TRIGGERS:
        rows.append(["", t])
    rows.append(["CUT AFTER QUARTERLY REVIEW:"])
    for t in QUARTERLY_REVIEW_CUT_TRIGGERS:
        rows.append(["", t])
    rows.append(["NEVER CUT BECAUSE:"])
    for t in NEVER_CUT_TRIGGERS:
        rows.append(["", t])

    ws.update(range_name="A1", values=rows)


def _write_moonshot_sheet(spreadsheet, moonshot):
    """Sheet 5: Moonshot scenarios and ETAs."""
    from portfolios.moonshot import RETURN_ETAS, RETURN_SCENARIOS

    ws = _get_or_create_worksheet(spreadsheet, "Moonshot Scenarios")

    rows = [
        ["MOONSHOT PORTFOLIO — RETURN SCENARIOS"],
        [],
    ]

    for scenario in RETURN_SCENARIOS:
        rows.append([f"{scenario.name} Case", "", f"Portfolio: ~{scenario.portfolio_multiple:.0f}x"])
        rows.append(["Ticker", "Multiple"])
        for t, m in scenario.multipliers.items():
            rows.append([t, f"{m}x"])
        rows.append([])

    rows.extend([["RETURN ETAs"], ["Ticker", "ETA", "Key Trigger"]])
    for t, info in RETURN_ETAS.items():
        rows.append([t, info["eta"], info["trigger"]])

    ws.update(range_name="A1", values=rows)


def _write_universe_sheet(spreadsheet):
    """Sheet 6: Full stock universe."""
    from data.stocks import UNIVERSE

    ws = _get_or_create_worksheet(spreadsheet, "Stock Universe")

    rows = [
        ["STOCK UNIVERSE — All Discussed (Apr 2-4, 2026)"],
        [],
        ["Ticker", "Name", "Sector", "Price", "Market Cap", "P/E",
         "Geo Risk", "Debt", "AI Thesis", "Notes"],
    ]

    for ticker in sorted(UNIVERSE):
        s = UNIVERSE[ticker]
        rows.append([
            s.ticker, s.name, s.sector.value,
            f"${s.price:.2f}" if s.price else "",
            f"${s.market_cap_millions:,.0f}M",
            f"{s.ttm_pe:.1f}x" if s.ttm_pe else "Loss/Trough",
            s.geopolitical_risk.value, s.debt_level.value,
            s.ai_thesis[:200], s.notes[:200],
        ])

    ws.update(range_name="A1", values=rows)


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Google Sheets Dashboard")
    parser.add_argument("--update", metavar="SHEET_ID", help="Update existing spreadsheet")
    parser.add_argument("--share", metavar="EMAIL", help="Email to share with")
    parser.add_argument(
        "--credentials",
        default=os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json"),
        help="Path to service account JSON key (default: credentials.json)",
    )
    args = parser.parse_args()

    url = create_dashboard(
        credentials_path=args.credentials,
        sheet_id=args.update,
        share_email=args.share,
    )
    print(f"\nDashboard URL: {url}")


if __name__ == "__main__":
    main()
