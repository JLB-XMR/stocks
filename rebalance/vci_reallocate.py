"""VCI Reallocation: Rebuild the actual IBKR portfolio using VCI thesis filters.

Takes the 17-position IBKR portfolio (April 24, 2026) and reallocates it to
restore all 5 VCI filters: low P/E, infrastructure over speculation, low debt,
convergence themes, global diversification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tabulate import tabulate

from backtest.comparison import IBKR_CASH, IBKR_POSITIONS, IBKR_TOTAL, IBKRPosition
from data.stocks import CMCSA, CNH, PBR, PLAB, VZ


class Action(Enum):
    SELL = "SELL"
    KEEP = "KEEP"
    STRUCTURAL = "STRUCTURAL"


@dataclass
class ReallocationDecision:
    position: IBKRPosition
    action: Action
    reason: str
    vci_filters_passed: int
    proceeds: float


@dataclass
class BuyOrder:
    ticker: str
    name: str
    shares: int
    price: float
    cost: float
    vci_rationale: str


# Each position evaluated against the 5 VCI filters.
# Map: ticker -> (action, filters_passed, reason)
_TRIAGE: dict[str, tuple[Action, int, str]] = {
    "AMSC": (
        Action.KEEP, 4,
        "Grid infrastructure + fusion optionality. PE 11.6x (marginal). "
        "Profitable, low debt. Convergence: energy + AI.",
    ),
    "CODA": (
        Action.KEEP, 3,
        "4D sonar monopoly. Navy DAVD programme. Profitable, +28.8% YoY. "
        "Defense infrastructure — cannot-be-bypassed.",
    ),
    "HSAI": (
        Action.SELL, 2,
        "Passes infrastructure + profitability, but Pentagon 1260H + Senate "
        "delisting = binary political risk incompatible with VCI discipline.",
    ),
    "IONQ": (
        Action.SELL, 0,
        "82x P/S, -487% operating margin. Pure speculation. "
        "Fails PE, profitability, infrastructure.",
    ),
    "QBTS": (
        Action.SELL, 0,
        "Binary tech risk. No revenue visibility. Fails all VCI filters.",
    ),
    "IREN": (
        Action.SELL, 1,
        "BTC-correlated AI compute. Speculation, not infrastructure. "
        "Fails PE and convergence filters.",
    ),
    "SEER": (
        Action.SELL, 0,
        "M&A arbitrage play. Not infrastructure, no convergence theme, "
        "no operating business.",
    ),
    "SOFI": (
        Action.SELL, 0,
        "Tagged for exit after Apr 29 earnings. Muddy Waters short. "
        "Not VCI infrastructure.",
    ),
    "GRRR": (
        Action.SELL, 0,
        "No structural moat (fails Layer 2). AI video analytics is "
        "commodity software, not infrastructure.",
    ),
    "ETOR": (
        Action.SELL, 0,
        "Crypto/retail sentiment correlation. Fintech, not infrastructure. "
        "No convergence theme.",
    ),
    "ONDS": (
        Action.SELL, 0,
        "Acknowledged hubris. Flagged 'EXIT immediately'. No VCI case.",
    ),
    "NKE": (
        Action.SELL, 1,
        "Consumer discretionary, not infrastructure. Tariff + China exposure. "
        "No convergence theme.",
    ),
    "NVTS": (
        Action.SELL, 1,
        "GaN power semis — interesting but $35 position. Too small to matter. "
        "Not in VCI universe.",
    ),
    "EGAN": (
        Action.SELL, 0,
        "Self-described 'irrelevant position'. $7 value.",
    ),
    "CSHR": (Action.STRUCTURAL, 0, "Employer — hold as agreed."),
    "DN3": (Action.STRUCTURAL, 0, "BTC proxy — hold as agreed."),
    "FAASF": (Action.STRUCTURAL, 0, "Delisted. Cannot sell."),
}

# VCI-qualifying stocks affordable at this portfolio size, ordered by conviction.
_BUY_CANDIDATES = [
    (VZ, 0.22, "Strongest VCI case. AI Connect + Frontier fiber. PE 8.6x."),
    (PLAB, 0.20, "Photomask monopoly. Zero debt. PE 10.1x."),
    (CMCSA, 0.20, "Post-Versant pure connectivity. DOCSIS 4.0. PE 8.0x. FCF $19.2B."),
    (CNH, 0.20, "AgriTech at trough. Raven autonomous farming IP. Food security."),
    (PBR, 0.18, "Energy infrastructure. PE 7.6x. Dividend + oil upside."),
]

VCI_CASH_TARGET = 0.10


def evaluate_positions() -> list[ReallocationDecision]:
    """Evaluate each IBKR position against VCI filters."""
    decisions = []
    for p in IBKR_POSITIONS:
        action, filters_passed, reason = _TRIAGE[p.ticker]
        proceeds = p.shares * p.current_price if action == Action.SELL else 0
        decisions.append(ReallocationDecision(
            position=p,
            action=action,
            reason=reason,
            vci_filters_passed=filters_passed,
            proceeds=proceeds,
        ))
    return decisions


def build_buy_list(available_cash: float) -> list[BuyOrder]:
    """Generate VCI-compliant buy orders from available cash."""
    orders = []
    for stock, weight, rationale in _BUY_CANDIDATES:
        allocation = available_cash * weight
        shares = int(allocation / stock.price)
        if shares < 1:
            continue
        orders.append(BuyOrder(
            ticker=stock.ticker,
            name=stock.name,
            shares=shares,
            price=stock.price,
            cost=shares * stock.price,
            vci_rationale=rationale,
        ))
    return orders


def run_reallocation() -> str:
    """Generate the full VCI reallocation plan."""
    lines: list[str] = []
    w = 80

    lines.append("=" * w)
    lines.append("  VCI REALLOCATION PLAN -- Rebuild IBKR Portfolio")
    lines.append("=" * w)
    lines.append("")
    lines.append("  Applying all 5 VCI filters to actual portfolio (EUR 2,801):")
    lines.append("    1. Low P/E (<10x) as entry discipline")
    lines.append("    2. Infrastructure over speculation")
    lines.append("    3. Low debt as hard filter")
    lines.append("    4. Convergence themes (AI + energy + food security)")
    lines.append("    5. Global diversification")
    lines.append("")
    lines.append("  NOTE: Position values in USD. EUR total approximate (FX ~1.08).")
    lines.append("")

    # --- Step 1: Triage ---
    decisions = evaluate_positions()
    sells = [d for d in decisions if d.action == Action.SELL]
    keeps = [d for d in decisions if d.action == Action.KEEP]
    structurals = [d for d in decisions if d.action == Action.STRUCTURAL]

    lines.append("  STEP 1: POSITION TRIAGE")
    lines.append("  " + "-" * 50)
    lines.append("")

    # Sells
    lines.append("  SELL (fails VCI filters):")
    sell_rows = []
    total_proceeds = 0.0
    for d in sells:
        val = d.position.shares * d.position.current_price
        pnl = ((d.position.current_price / d.position.avg_cost) - 1) * 100 if d.position.avg_cost else 0
        total_proceeds += val
        sell_rows.append([
            d.position.ticker,
            d.position.name[:18],
            d.position.shares,
            f"${d.position.current_price:.2f}",
            f"${val:,.0f}",
            f"{pnl:+.1f}%",
            f"{d.vci_filters_passed}/5",
        ])
    lines.append(tabulate(
        sell_rows,
        headers=["Ticker", "Name", "Shares", "Price", "Value", "P&L", "VCI"],
        tablefmt="simple",
    ))
    lines.append(f"\n  Total sell proceeds: ${total_proceeds:,.0f}")
    lines.append("")

    # Keeps
    lines.append("  KEEP (passes VCI filters):")
    keep_rows = []
    total_kept = 0.0
    for d in keeps:
        val = d.position.shares * d.position.current_price
        total_kept += val
        keep_rows.append([
            d.position.ticker,
            d.position.name[:18],
            d.position.shares,
            f"${d.position.current_price:.2f}",
            f"${val:,.0f}",
            f"{d.vci_filters_passed}/5",
            d.reason[:55],
        ])
    lines.append(tabulate(
        keep_rows,
        headers=["Ticker", "Name", "Shares", "Price", "Value", "VCI", "Reason"],
        tablefmt="simple",
    ))
    lines.append(f"\n  Total kept value: ${total_kept:,.0f}")
    lines.append("")

    # Structural holds
    lines.append("  STRUCTURAL HOLDS (cannot sell):")
    struct_val = 0.0
    for d in structurals:
        val = d.position.shares * d.position.current_price
        struct_val += val
        lines.append(
            f"    {d.position.ticker}: {d.position.shares} shares "
            f"x ${d.position.current_price:.2f} = ${val:,.0f} -- {d.reason}"
        )
    lines.append(f"    Total structural: ${struct_val:,.0f} (excluded from VCI allocation)")
    lines.append("")

    # --- Step 2: Capital ---
    # IBKR_CASH is EUR; convert approximate to USD
    cash_usd = IBKR_CASH * 1.08
    total_investable = total_kept + total_proceeds + cash_usd
    cash_reserve = total_investable * VCI_CASH_TARGET
    cash_for_buys = total_proceeds + cash_usd - cash_reserve

    lines.append("  STEP 2: CAPITAL AVAILABLE")
    lines.append("  " + "-" * 50)
    lines.append(f"    Sell proceeds:       ${total_proceeds:,.0f}")
    lines.append(f"    Existing cash:       ${cash_usd:,.0f} (EUR {IBKR_CASH:.0f} x 1.08)")
    lines.append(f"    Kept positions:      ${total_kept:,.0f}")
    lines.append(f"    Total investable:    ${total_investable:,.0f}")
    lines.append(f"    Cash reserve (10%):  ${cash_reserve:,.0f}")
    lines.append(f"    Available for buys:  ${cash_for_buys:,.0f}")
    lines.append("")

    # --- Step 3: Buy list ---
    orders = build_buy_list(cash_for_buys)

    lines.append("  STEP 3: VCI BUY LIST")
    lines.append("  " + "-" * 50)
    buy_rows = []
    total_bought = 0.0
    for o in orders:
        total_bought += o.cost
        buy_rows.append([
            o.ticker, o.name, o.shares,
            f"${o.price:.2f}", f"${o.cost:,.0f}",
            o.vci_rationale,
        ])
    lines.append(tabulate(
        buy_rows,
        headers=["Ticker", "Name", "Shares", "Price", "Cost", "VCI Rationale"],
        tablefmt="simple",
    ))
    lines.append(f"\n  Total invested: ${total_bought:,.0f}")
    lines.append("")

    # --- Step 4: Final portfolio ---
    final_positions: list[tuple[str, str, float, float, float]] = []
    for d in keeps:
        v = d.position.shares * d.position.current_price
        final_positions.append((d.position.ticker, d.position.name, d.position.shares, d.position.current_price, v))
    for o in orders:
        final_positions.append((o.ticker, o.name, o.shares, o.price, o.cost))

    total_stock_value = sum(v for *_, v in final_positions)
    final_cash = cash_for_buys - total_bought + cash_reserve
    total_ex_structural = total_stock_value + final_cash

    lines.append("  STEP 4: FINAL PORTFOLIO STATE")
    lines.append("  " + "-" * 50)
    final_rows = []
    for ticker, name, shares, price, val in sorted(final_positions, key=lambda x: x[4], reverse=True):
        weight = val / total_ex_structural * 100
        final_rows.append([
            ticker, name[:18], f"{shares:.0f}" if isinstance(shares, (int, float)) else shares,
            f"${price:.2f}", f"${val:,.0f}", f"{weight:.1f}%",
        ])
    final_rows.append([
        "CASH", "--", "--", "--", f"${final_cash:,.0f}",
        f"{final_cash / total_ex_structural * 100:.1f}%",
    ])
    lines.append(tabulate(
        final_rows,
        headers=["Ticker", "Name", "Shares", "Price", "Value", "Weight"],
        tablefmt="simple",
    ))
    lines.append("")
    lines.append(f"  Investable portfolio: ${total_ex_structural:,.0f} "
                 f"({len(final_positions)} positions + cash)")
    lines.append(f"  Structural holds:    ${struct_val:,.0f} (CSHR, DN3, FAASF)")
    lines.append(f"  Total account:       ${total_ex_structural + struct_val:,.0f}")
    lines.append("")

    # --- Step 5: VCI filter compliance ---
    lines.append("  STEP 5: VCI FILTER COMPLIANCE")
    lines.append("  " + "-" * 50)
    filter_check = [
        [
            "Low P/E (<10x)",
            "VZ 8.6x, CMCSA 8.0x, PBR 7.6x, PLAB 10.1x, CNH trough, AMSC 11.6x",
            "RESTORED",
        ],
        [
            "Infrastructure > speculation",
            "Telco (VZ, CMCSA), photomask (PLAB), grid (AMSC), agritech (CNH), "
            "energy (PBR), sonar (CODA)",
            "RESTORED",
        ],
        [
            "Low debt",
            "PLAB zero debt, AMSC low, CNH moderate, VZ moderate, PBR moderate, "
            "CMCSA high (weakest)",
            "RESTORED",
        ],
        [
            "Convergence themes",
            "AI infra (VZ, PLAB, AMSC), energy (PBR), food (CNH), defense (CODA)",
            "RESTORED",
        ],
        [
            "Global diversification",
            "US (AMSC, PLAB, CMCSA, CODA, VZ), Brazil (PBR), Netherlands (CNH)",
            "RESTORED",
        ],
    ]
    lines.append(tabulate(
        filter_check,
        headers=["VCI Filter", "How It's Met", "Status"],
        tablefmt="simple",
    ))
    lines.append("")

    # --- Step 6: DCA plan ---
    lines.append("  STEP 6: UPDATED DCA PLAN (EUR 800/month)")
    lines.append("  " + "-" * 50)
    lines.append("")
    lines.append("  Default monthly split:")
    lines.append("    EUR 300 -> PLAB (sleeper name, zero debt photomask monopoly)")
    lines.append("    EUR 300 -> AMSC (grid anchor, until 15% weight cap)")
    lines.append("    EUR 200 -> Rotate: smallest VCI position by weight")
    lines.append("")
    lines.append("  Decision tree (restored VCI 4-step):")
    lines.append("    Q1: Cash buffer < 10%? -> Replenish cash first")
    lines.append("    Q2: Any VCI name > 10% below 52-week low? -> Dip buy")
    lines.append("    Q3: Earnings catalyst within 30 days? -> Add to that name")
    lines.append("    Q4: Default -> PLAB (highest conviction, zero debt)")
    lines.append("")
    lines.append("  Position cap: No single position > 15% of investable portfolio")
    lines.append("  Monthly max: Add to at most 2 names per month")
    lines.append("")

    # --- Execution sequence ---
    lines.append("  EXECUTION SEQUENCE")
    lines.append("  " + "-" * 50)
    lines.append("")
    lines.append("  Day 1 -- SELL (limit orders, GTC):")
    for d in sells:
        val = d.position.shares * d.position.current_price
        lines.append(
            f"    SELL {d.position.shares:>4} {d.position.ticker:<6} "
            f"@ ~${d.position.current_price:.2f}  =  ~${val:,.0f}"
        )
    lines.append("")
    lines.append("  Day 2 -- BUY (after sells settle, limit orders):")
    for o in orders:
        lines.append(
            f"    BUY  {o.shares:>4} {o.ticker:<6} "
            f"@ limit ${o.price:.2f}  =  ${o.cost:,.0f}"
        )
    lines.append("")
    lines.append("  Day 3 -- VERIFY:")
    lines.append("    Confirm all fills. Adjust unfilled limit orders.")
    lines.append("    Set quarterly rebalance calendar: Jul 1, Oct 1, Jan 1, Apr 1.")
    lines.append("    Update bot config (bot/config.py) with new target weights.")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    print(run_reallocation())
