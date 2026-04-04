"""DCA (Dollar-Cost Averaging) decision tree and monthly addition logic.

Implements the documented decision tree for EUR 200-300/month additions.
"""

from dataclasses import dataclass

from data.models import Portfolio


@dataclass
class DCADecision:
    action: str
    ticker: str | None
    amount: float
    reason: str


def decide_monthly_addition(
    portfolio: Portfolio,
    monthly_amount: float,
    cash_minimum: float = 100.0,
    positions_down_35pct: list[str] | None = None,
    thesis_changed: list[str] | None = None,
    positive_catalyst_this_month: str | None = None,
    default_ticker: str = "ARQQ",
) -> DCADecision:
    """Run the DCA decision tree for a monthly addition.

    Decision tree:
        Q1: Is cash reserve below minimum? -> Put entire addition into cash.
        Q2: Is any position down >35% since last buy WITHOUT thesis change? -> Buy that.
        Q3: Which moonshot had a confirmed positive catalyst this month? -> Buy that.
        Q4: Default -> Buy ARQQ.

    Args:
        portfolio: Current portfolio state
        monthly_amount: Amount to invest this month
        cash_minimum: Minimum cash reserve threshold
        positions_down_35pct: Tickers down >35% since last buy
        thesis_changed: Tickers whose thesis has changed (exclude from Q2)
        positive_catalyst_this_month: Ticker with confirmed catalyst

    Returns:
        DCADecision with the recommended action
    """
    if positions_down_35pct is None:
        positions_down_35pct = []
    if thesis_changed is None:
        thesis_changed = []

    # Q1: Cash reserve check
    if portfolio.cash < cash_minimum:
        return DCADecision(
            action="ADD_TO_CASH",
            ticker=None,
            amount=monthly_amount,
            reason=f"Cash reserve (${portfolio.cash:.0f}) below ${cash_minimum:.0f} minimum",
        )

    # Q2: Position down >35% without thesis change
    eligible_dips = [t for t in positions_down_35pct if t not in thesis_changed]
    if eligible_dips:
        target = eligible_dips[0]  # buy the first/most down
        return DCADecision(
            action="BUY_DIP",
            ticker=target,
            amount=monthly_amount,
            reason=f"{target} down >35% since last buy, thesis intact",
        )

    # Q3: Positive catalyst this month
    if positive_catalyst_this_month:
        return DCADecision(
            action="BUY_CATALYST",
            ticker=positive_catalyst_this_month,
            amount=monthly_amount,
            reason=f"{positive_catalyst_this_month} had confirmed positive catalyst",
        )

    # Q4: Default to ARQQ
    return DCADecision(
        action="BUY_DEFAULT",
        ticker=default_ticker,
        amount=monthly_amount,
        reason=f"No special conditions — default to {default_ticker}",
    )


# Rules: things to NEVER do with monthly additions
DCA_NEVER_RULES = [
    "Spread across 6 positions — that's noise at this portfolio size",
    "Chase a position up >60% in 90 days",
    "Add to a position you're already doubting",
]
