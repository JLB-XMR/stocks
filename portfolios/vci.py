"""Portfolio 1 — Value Convergence Index (VCI).

9 stocks + 10% cash | Quarterly rebalancing | EUR 1,000 base.

Meta-thesis: "Cheap entry on unglamorous, cash-generating businesses that become
critical infrastructure as AI, energy transition, and food security converge —
priced as if none of that transformation happens."
"""

from data.models import Portfolio, PortfolioTier, Position
from data.stocks import AGCO, C, CMCSA, CNH, IPGP, PBR, PLAB, TRMB, VZ

PORTFOLIO_NAME = "Value Convergence Index (VCI)"
BASE_CURRENCY = "EUR"
BASE_AMOUNT = 1_000.0
CASH_WEIGHT = 0.107
REBALANCE_FREQUENCY = "quarterly"  # Jan, Apr, Jul, Oct
DRIFT_THRESHOLD = 0.05  # 5% drift triggers rebalance


def build_vci_portfolio() -> Portfolio:
    """Construct the VCI portfolio with target weights and entry prices."""
    positions = [
        Position(
            stock=VZ,
            shares=0,  # calculated at deployment
            entry_price=43.00,
            cost_basis=0,
            weight=0.126,
            tier=PortfolioTier.VCI_VALUE,
        ),
        Position(
            stock=C,
            shares=0,
            entry_price=65.00,
            cost_basis=0,
            weight=0.091,
            tier=PortfolioTier.VCI_VALUE,
        ),
        Position(
            stock=CMCSA,
            shares=0,
            entry_price=40.00,
            cost_basis=0,
            weight=0.105,
            tier=PortfolioTier.VCI_VALUE,
        ),
        Position(
            stock=PBR,
            shares=0,
            entry_price=16.00,
            cost_basis=0,
            weight=0.101,
            tier=PortfolioTier.VCI_VALUE,
        ),
        Position(
            stock=PLAB,
            shares=0,
            entry_price=22.00,
            cost_basis=0,
            weight=0.088,
            tier=PortfolioTier.VCI_BRIDGE,
        ),
        Position(
            stock=IPGP,
            shares=0,
            entry_price=85.00,
            cost_basis=0,
            weight=0.096,
            tier=PortfolioTier.VCI_VALUE,
        ),
        Position(
            stock=AGCO,
            shares=0,
            entry_price=100.00,
            cost_basis=0,
            weight=0.096,
            tier=PortfolioTier.VCI_VALUE,
        ),
        Position(
            stock=CNH,
            shares=0,
            entry_price=12.00,
            cost_basis=0,
            weight=0.095,
            tier=PortfolioTier.VCI_VALUE,
        ),
        Position(
            stock=TRMB,
            shares=0,
            entry_price=55.00,
            cost_basis=0,
            weight=0.096,
            tier=PortfolioTier.VCI_VALUE,
        ),
    ]

    cash = BASE_AMOUNT * CASH_WEIGHT

    # Calculate shares and cost basis from weights
    for pos in positions:
        allocated = BASE_AMOUNT * pos.weight
        pos.shares = allocated / pos.entry_price
        pos.cost_basis = pos.shares * pos.entry_price

    return Portfolio(
        name=PORTFOLIO_NAME,
        positions=positions,
        cash=cash,
        total_value=BASE_AMOUNT,
        currency=BASE_CURRENCY,
        description=(
            "9 stocks + 10% cash. Quarterly rebalancing. "
            "Filter: low P/E, infrastructure over speculation, "
            "convergence themes, low debt, global diversification."
        ),
    )


# CoinShares model portfolio benchmarks for comparison
COINSHARES_BENCHMARKS = {
    "BTC0": {"annual_perf": 0.048, "vol": 0.123, "sharpe": 0.39, "max_dd": -0.241},
    "BTC50": {"annual_perf": 0.082, "vol": 0.122, "sharpe": 0.67, "max_dd": -0.257},
    "BTCETH": {"annual_perf": 0.087, "vol": 0.125, "sharpe": 0.70, "max_dd": -0.266},
    "TOP50": {"annual_perf": 0.094, "vol": 0.125, "sharpe": 0.75, "max_dd": -0.264},
}
