"""Portfolio 2 — $1,500 Moonshot.

Target: 50-75x | 5-7 year horizon.
Three tiers: moonshots carry the return target; bridge positions provide
real earnings floor; cash reserve for tactical deployment.
"""

from data.models import Portfolio, PortfolioTier, Position, ReturnScenario
from data.stocks import AMSC, ARQQ, NNOX, PLAB, POET

PORTFOLIO_NAME = "Moonshot Portfolio"
BASE_CURRENCY = "USD"
BASE_AMOUNT = 1_500.0
CASH_RESERVE = 146.0


def build_moonshot_portfolio() -> Portfolio:
    """Construct the $1,500 Moonshot portfolio."""
    positions = [
        Position(
            stock=ARQQ,
            shares=44,
            entry_price=13.97,
            cost_basis=615.0,
            weight=0.410,
            tier=PortfolioTier.MOONSHOT,
        ),
        Position(
            stock=POET,
            shares=55,
            entry_price=6.11,
            cost_basis=336.0,
            weight=0.224,
            tier=PortfolioTier.MOONSHOT,
        ),
        Position(
            stock=NNOX,
            shares=62,
            entry_price=2.42,
            cost_basis=150.0,
            weight=0.100,
            tier=PortfolioTier.MOONSHOT,
        ),
        Position(
            stock=AMSC,
            shares=4,
            entry_price=32.65,
            cost_basis=131.0,
            weight=0.087,
            tier=PortfolioTier.BRIDGE,
        ),
        Position(
            stock=PLAB,
            shares=3,
            entry_price=40.70,
            cost_basis=122.0,
            weight=0.081,
            tier=PortfolioTier.VCI_BRIDGE,
        ),
    ]

    return Portfolio(
        name=PORTFOLIO_NAME,
        positions=positions,
        cash=CASH_RESERVE,
        total_value=BASE_AMOUNT,
        currency=BASE_CURRENCY,
        description=(
            "$1,500 moonshot vehicle. 41% ARQQ concentration is the feature. "
            "Target 50-75x over 5-7 years."
        ),
    )


# Return scenario projections
RETURN_SCENARIOS = [
    ReturnScenario(
        name="Bull",
        multipliers={"ARQQ": 100, "POET": 50, "NNOX": 75, "AMSC": 15, "PLAB": 10},
        portfolio_multiple=62.0,
    ),
    ReturnScenario(
        name="Base",
        multipliers={"ARQQ": 25, "POET": 15, "NNOX": 20, "AMSC": 8, "PLAB": 6},
        portfolio_multiple=18.0,
    ),
    ReturnScenario(
        name="Bear",
        multipliers={"ARQQ": 0, "POET": 0, "NNOX": 0, "AMSC": 3, "PLAB": 2},
        portfolio_multiple=0.9,
    ),
]

# Deployment calendar
DEPLOYMENT_CALENDAR = [
    {
        "date": "2026-04-06",
        "action": "Deploy ARQQ (44), POET (55), AMSC (4), PLAB (3) at market open",
    },
    {
        "date": "2026-04-06",
        "action": "NNOX earnings day — watch reaction, do NOT buy blind",
    },
    {
        "date": "2026-04-07",
        "action": "If NNOX earnings positive → deploy 62 shares. If negative → hold cash",
    },
]

# ETA estimates for max returns
RETURN_ETAS = {
    "ARQQ": {"eta": "2031-2034", "trigger": "Gov/telco procurement scaling; or M&A (2-3yr)"},
    "POET": {"eta": "2030-2033", "trigger": "CPO universal standard; or M&A"},
    "NNOX": {"eta": "2029-2032", "trigger": "Hospital adoption; or cash runs out 12-15mo"},
    "AMSC": {"eta": "2031-2034", "trigger": "Grid modernisation + fusion deployment"},
    "PLAB": {"eta": "2032-2035", "trigger": "Node migration + Texas/Korea expansion"},
}
