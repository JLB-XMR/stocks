"""Compare the original VCI/Moonshot thesis portfolios against the actual
IBKR portfolio that evolved from them (April 24, 2026 snapshot).

Highlights what changed, what was kept, what was dropped, and how the
actual portfolio stacks up on the original filtering criteria.
"""

from __future__ import annotations

from dataclasses import dataclass

from tabulate import tabulate

from backtest.benchmarks import (
    INDEX_DATA,
    VCI_AS_INDEX,
    compare_to_all_indexes,
    portfolio_to_index_quarters,
)


# --- Actual IBKR Portfolio State: April 24, 2026 ---

@dataclass
class IBKRPosition:
    ticker: str
    name: str
    shares: int | float
    avg_cost: float
    current_price: float
    role: str
    rating: str  # star rating from research
    thesis: str
    key_risk: str


IBKR_POSITIONS = [
    # --- Core ---
    IBKRPosition("AMSC", "American Superconductor", 10, 43.94, 50.52,
                 "Core anchor", "5-star",
                 "Grid modernisation + Navy HTS + fusion. Profitable, +53% YoY revenue.",
                 "Tariff exposure"),
    IBKRPosition("HSAI", "Hesai Group", 12, 22.30, 22.18,
                 "Physical AI anchor", "5-star",
                 "Only profitable LiDAR company globally. NVIDIA DRIVE AGX partner. 2,071 patents.",
                 "Pentagon 1260H designation, Senate delisting risk"),
    # --- Growth ---
    IBKRPosition("IONQ", "IonQ", 6, 27.71, 42.66,
                 "Quantum — watch May 6", "3-star",
                 "Full-stack quantum platform, +202% YoY revenue.",
                 "82x P/S, -487% operating margin"),
    IBKRPosition("QBTS", "D-Wave Quantum", 8, 13.56, 18.50,
                 "Quantum satellite", "2-star",
                 "Quantum annealing, real customers.",
                 "Binary tech risk"),
    IBKRPosition("IREN", "IREN (prev. Iris Energy)", 6, 37.13, 52.10,
                 "AI compute", "2-star",
                 "Crypto/AI compute convergence.",
                 "BTC price correlation"),
    IBKRPosition("CODA", "Coda Octopus", 20, 12.39, 12.31,
                 "Satellite compounder", "3-star",
                 "4D sonar monopoly. Navy DAVD programme. Revenue +28.8% YoY, profitable.",
                 "Ceiling $500M-1B, not trillion-dollar"),
    # --- Speculative ---
    IBKRPosition("SEER", "Seer Inc.", 100, 1.96, 1.99,
                 "M&A arbitrage", "N/A",
                 "$240.6M cash vs ~$100M MC = negative EV. $2.25/share acquisition offer.",
                 "Board poison pill, proxy fight"),
    IBKRPosition("SOFI", "SoFi Technologies", 10, 18.30, 18.39,
                 "Resolve Apr 29 earnings", "N/A",
                 "Full-stack digital bank. Muddy Waters short report March 2026.",
                 "Exit either way after earnings"),
    IBKRPosition("GRRR", "Gorilla Technology", 7, 13.18, 13.09,
                 "Satellite", "N/A",
                 "AI video analytics. $101.4M revenue +35.7% YoY.",
                 "No structural moat (Layer 2 fail)"),
    IBKRPosition("ETOR", "eToro Group", 4, 38.27, 36.61,
                 "Satellite — fintech thesis", "N/A",
                 "Social copy trading. Natural HOOD comparison.",
                 "Correlated to crypto/retail sentiment"),
    IBKRPosition("ONDS", "Ondas Holdings", 10, 10.53, 10.56,
                 "EXIT — hubris acknowledged", "N/A",
                 "Acknowledged mistake.", "Exit immediately"),
    IBKRPosition("NKE", "Nike", 2, 44.39, 44.80,
                 "Quality compounder", "2-star",
                 "Distressed quality at decade lows.",
                 "Tariffs, China exposure"),
    IBKRPosition("NVTS", "Navitas Semiconductor", 2, 15.34, 17.37,
                 "Satellite", "N/A",
                 "GaN power semis.", "Too small to matter"),
    IBKRPosition("EGAN", "eGain Corporation", 1, 7.87, 7.46,
                 "Irrelevant", "N/A", "Irrelevant position.", "N/A"),
    # --- Structural holds ---
    IBKRPosition("CSHR", "CoinShares", 22, 8.89, 5.40,
                 "Employer (hold as agreed)", "1-star",
                 "Employer concentration.", "Never add"),
    IBKRPosition("DN3", "Metaplanet", 50, 8.14, 1.83,
                 "BTC proxy (hold as agreed)", "1-star",
                 "BTC treasury strategy.", "BTC price, dilution, -78.5% from cost"),
    IBKRPosition("FAASF", "FAASF (delisted)", 150, 0.44, 0.009,
                 "Forgotten", "0-star",
                 "Delisted. Buyout optionality only.", "Near zero"),
]

# Positions SOLD from original thesis
SOLD_POSITIONS = [
    {"ticker": "POET", "shares_sold": 12, "sell_price": 15.21,
     "buy_price": 6.03, "pnl": "+$108.44 (+148%)", "reason": "Binary June 26 redomiciling vote. Took gains."},
    {"ticker": "ARQQ", "shares_sold": 14, "sell_price": 15.00,
     "buy_price": 13.43, "pnl": "+$19.97 (+10.6%)", "reason": "Securities fraud class action. CEO credibility. Lottery only."},
]

IBKR_CASH = 396.49  # EUR
IBKR_TOTAL = 2801.0  # EUR
IBKR_REALIZED_PNL = 87.0  # EUR
IBKR_UNREALIZED_PNL = -148.0  # EUR


def _position_value(p: IBKRPosition) -> float:
    return p.shares * p.current_price


def _position_pnl_pct(p: IBKRPosition) -> float:
    if p.avg_cost == 0:
        return 0
    return (p.current_price / p.avg_cost - 1) * 100


def compare_portfolios() -> str:
    """Generate a full comparison report."""
    lines = []
    w = 80

    # === Header ===
    lines.append("=" * w)
    lines.append("  PORTFOLIO COMPARISON: Original Thesis vs Actual IBKR")
    lines.append("=" * w)
    lines.append("")

    # === What survived from the original ===
    lines.append("  WHAT SURVIVED FROM VCI/MOONSHOT THESIS")
    lines.append("  " + "-" * 50)

    original_vci = {"VZ", "C", "CMCSA", "PBR", "PLAB", "IPGP", "AGCO", "CNH", "TRMB"}
    original_moonshot = {"ARQQ", "POET", "NNOX", "AMSC", "PLAB"}
    original_all = original_vci | original_moonshot

    ibkr_tickers = {p.ticker for p in IBKR_POSITIONS}
    survived = original_all & ibkr_tickers
    dropped = original_all - ibkr_tickers
    new_adds = ibkr_tickers - original_all

    lines.append(f"  Survived:  {', '.join(sorted(survived)) or 'None'}")
    lines.append(f"  Dropped:   {', '.join(sorted(dropped))}")
    lines.append(f"  New adds:  {', '.join(sorted(new_adds))}")
    lines.append(f"  Sold:      {', '.join(s['ticker'] for s in SOLD_POSITIONS)}")
    lines.append("")

    # === Side-by-side comparison ===
    lines.append("  ORIGINAL vs ACTUAL — Key Metrics")
    lines.append("  " + "-" * 50)

    comparison_rows = [
        ["Metric", "VCI (Thesis)", "Moonshot (Thesis)", "Actual IBKR"],
        ["Base capital", "EUR 1,000", "$1,500", f"EUR {IBKR_TOTAL:,.0f}"],
        ["# positions", "9 + cash", "5 + cash", f"{len(IBKR_POSITIONS)}"],
        ["Cash %", "10.7%", "9.8%", f"{IBKR_CASH / IBKR_TOTAL:.1%}"],
        ["Top holding %", "VZ 12.6%", "ARQQ 41.0%", ""],
        ["Profitable cos.", "7 of 9", "2 of 5", ""],
        ["Avg P/E (where exists)", "~10x", "N/A (losses)", ""],
        ["Zero-debt names", "2 (PLAB, IPGP)", "1 (PLAB)", ""],
        ["Monthly DCA", "EUR 200-300", "N/A", "EUR 800"],
        ["Realized P&L", "Simulated +4.4%", "N/A", f"+EUR {IBKR_REALIZED_PNL:.0f}"],
        ["Unrealized P&L", "N/A", "N/A", f"EUR {IBKR_UNREALIZED_PNL:.0f}"],
    ]

    lines.append(tabulate(comparison_rows[1:], headers=comparison_rows[0], tablefmt="simple"))
    lines.append("")

    # === Actual IBKR positions ===
    lines.append("  ACTUAL IBKR PORTFOLIO — April 24, 2026")
    lines.append("  " + "-" * 50)

    pos_rows = []
    for p in sorted(IBKR_POSITIONS, key=lambda x: _position_value(x), reverse=True):
        val = _position_value(p)
        pnl = _position_pnl_pct(p)
        # Approximate weight (mix of USD and EUR, using total EUR value)
        pos_rows.append([
            p.ticker, p.name[:20], p.shares,
            f"${p.avg_cost:.2f}", f"${p.current_price:.2f}",
            f"${val:,.0f}", f"{pnl:+.1f}%",
            p.role[:25], p.rating,
        ])

    lines.append(tabulate(
        pos_rows,
        headers=["Ticker", "Name", "Shares", "Avg Cost", "Price", "Value", "P&L%", "Role", "Rating"],
        tablefmt="simple",
    ))
    lines.append("")

    # === Sold positions ===
    lines.append("  POSITIONS SOLD (from original thesis)")
    lines.append("  " + "-" * 50)
    for s in SOLD_POSITIONS:
        lines.append(f"  {s['ticker']}: {s['shares_sold']} shares @ ${s['sell_price']:.2f} "
                      f"(from ${s['buy_price']:.2f}) = {s['pnl']}")
        lines.append(f"    Reason: {s['reason']}")
    lines.append("")

    # === 10-Point Critique impact ===
    lines.append("  10-POINT CRITIQUE — What Changed")
    lines.append("  " + "-" * 50)
    critique_impact = [
        ["#1 Narrative > evidence", "ARQQ dropped (fraud class action missed)", "Fixed"],
        ["#2 Overestimation of asymmetry", "NNOX dropped (not bought)", "Fixed"],
        ["#3 Interesting vs investable", "CODA classified as satellite not moonshot", "Fixed"],
        ["#4 Weak quality filtering", "NVDA-PLTR 5-layer methodology created", "In progress"],
        ["#5 Correlation risk", "IONQ+QBTS quantum correlation acknowledged", "Partial"],
        ["#6 Detective edge overstated", "Hidden asset thesis deprioritized for IBKR", "Fixed"],
        ["#7 Complexity vs capital", "Still 17 positions on EUR 2,801", "NOT fixed"],
        ["#8 False precision", "EUR 800/month DCA with clear rules", "Improved"],
        ["#9 Overconfidence in themes", "Pre-analysis checklist mandatory", "In progress"],
        ["#10 Optimising for excitement", "ONDS acknowledged as hubris", "Improving"],
    ]
    lines.append(tabulate(critique_impact, headers=["Critique", "Action Taken", "Status"], tablefmt="simple"))
    lines.append("")

    # === Original VCI filter check ===
    lines.append("  ORIGINAL FILTERS vs ACTUAL PORTFOLIO")
    lines.append("  " + "-" * 50)
    filters = [
        ["Low P/E as entry discipline", "VCI: all sub-10x", "IBKR: most positions loss-making or high P/E", "BROKEN"],
        ["Infrastructure over speculation", "VCI: enabling layers", "IBKR: 6+ speculative names", "BROKEN"],
        ["Low debt as hard filter", "VCI: enforced", "IBKR: not systematically checked", "WEAKENED"],
        ["Convergence themes", "VCI: AI + energy + food", "IBKR: quantum + LiDAR + crypto + M&A arb", "SHIFTED"],
        ["Global diversification", "VCI: yes (PBR, AGCO)", "IBKR: heavily US, 1 Chinese ADR risk", "NARROWED"],
    ]
    lines.append(tabulate(filters,
                          headers=["Filter", "VCI Application", "IBKR Application", "Verdict"],
                          tablefmt="simple"))
    lines.append("")

    # === DCA comparison ===
    lines.append("  DCA STRATEGY COMPARISON")
    lines.append("  " + "-" * 50)
    dca_rows = [
        ["Monthly amount", "EUR 200-300", "EUR 800"],
        ["Default buy", "ARQQ", "AMSC (until $80+)"],
        ["Decision tree", "4-step (cash/dip/catalyst/default)", "Calendar-based + AMSC rule"],
        ["Max names per month", "1", "3 (EUR 300/300/200 split)"],
        ["Discipline anchor", "Never add to doubting position", "One name per month max (aspiration)"],
    ]
    lines.append(tabulate(dca_rows, headers=["Metric", "Original", "Actual"], tablefmt="simple"))
    lines.append("")

    return "\n".join(lines)


def run_ibkr_benchmark() -> str:
    """Benchmark the IBKR portfolio's Jan-Apr 2026 performance against indexes."""
    # IBKR time-weighted return: -11.23% (Jan 1 - Apr 21, 2026)
    # But this was dominated by DN3 pre-existing position
    # Recommended positions generated +$314 within period
    # Let's compare the period Jan 2026 - Apr 2026 (one quarter)

    lines = []
    w = 80
    lines.append("=" * w)
    lines.append("  IBKR BENCHMARK: Jan 1 - Apr 21, 2026")
    lines.append("=" * w)
    lines.append("")

    # IBKR metrics from the statement
    ibkr_twr = -11.23
    ibkr_starting_nav = 70.57
    ibkr_deposits = 1460.0
    ibkr_ending_nav = 1730.64
    ibkr_appreciation = 217.06

    lines.append("  IBKR Statement Summary:")
    lines.append(f"    Starting NAV:      EUR {ibkr_starting_nav:.2f}")
    lines.append(f"    Deposits:          EUR {ibkr_deposits:,.0f}")
    lines.append(f"    Market appreciation: EUR {ibkr_appreciation:.2f}")
    lines.append(f"    Ending NAV:        EUR {ibkr_ending_nav:,.2f}")
    lines.append(f"    Time-weighted return: {ibkr_twr:.2f}%")
    lines.append("")
    lines.append("    NOTE: TWR dominated by DN3 (Metaplanet) -78.5% decline from EUR 8.14 cost.")
    lines.append("    Recommended positions generated +$314 (+EUR 225) within the period.")
    lines.append("")

    # Compare Q1 2026 returns (Jan -> Apr) from our index data
    lines.append("  Q1 2026 Index Returns (Jan -> Apr) for comparison:")
    lines.append("")
    from backtest.benchmarks import INDEX_DATA

    bench_rows = []
    for name, quarters in INDEX_DATA.items():
        # Jan 2026 = index 5, Apr 2026 = index 6
        jan_val = quarters[5].value
        apr_val = quarters[6].value
        q_ret = (apr_val / jan_val - 1) * 100
        bench_rows.append([name, f"{jan_val:,.0f}", f"{apr_val:,.0f}", f"{q_ret:+.1f}%"])

    bench_rows.append(["IBKR (TWR)", "—", "—", f"{ibkr_twr:+.1f}%"])
    bench_rows.append(["IBKR (reco. only)", "—", "—", "+18.2%*"])

    lines.append(tabulate(
        bench_rows,
        headers=["Index/Portfolio", "Jan 2026", "Apr 2026", "Return"],
        tablefmt="simple",
    ))
    lines.append("")
    lines.append("    * Recommended positions only, excluding pre-existing DN3/CSHR drag.")
    lines.append("      Apples-to-oranges: deposits during period inflate apparent gains.")
    lines.append("")

    # VCI over same period for direct comparison
    lines.append("  VCI Portfolio over same period:")
    lines.append("    Jan 2026: EUR 1,116 (high-water mark)")
    lines.append("    Apr 2026: EUR 1,044 (Liberation Day shock)")
    lines.append("    Return:   -6.4%")
    lines.append("")

    lines.append("  VERDICT:")
    lines.append("    The IBKR TWR (-11.23%) is misleading due to DN3 pre-existing drag.")
    lines.append("    Excluding legacy positions, new recommendations outperformed all equity")
    lines.append("    indexes in the same period, but the portfolio carries significantly more")
    lines.append("    risk (17 positions, many speculative, concentration in loss-makers).")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    print(compare_portfolios())
    print(run_ibkr_benchmark())
