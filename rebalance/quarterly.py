"""Quarterly rebalancing engine.

Aligns with earnings seasons: Jan, Apr, Jul, Oct.
Implements the four rebalancing questions from the research document.
"""

from dataclasses import dataclass

from data.models import Portfolio, Position


@dataclass
class RebalanceAction:
    question: str
    triggered: bool
    ticker: str | None
    action: str
    detail: str


def check_mcap_without_revenue(
    position: Position,
    current_mcap_millions: float,
    mcap_threshold_millions: float = 3_000,
    revenue_growth_pct: float = 0,
) -> RebalanceAction:
    """Q1: Has any position's market cap exceeded threshold without proportional revenue?

    If MC > threshold and revenue growth doesn't justify it, trim 50%.
    """
    triggered = (
        current_mcap_millions > mcap_threshold_millions
        and revenue_growth_pct < 50  # arbitrary: revenue should grow meaningfully
    )
    return RebalanceAction(
        question="Q1: Market cap exceeded $3B without proportional revenue?",
        triggered=triggered,
        ticker=position.stock.ticker,
        action="TRIM_50PCT" if triggered else "HOLD",
        detail=(
            f"{position.stock.ticker} MC ${current_mcap_millions:.0f}M with "
            f"{revenue_growth_pct:.0f}% revenue growth → trim 50%"
            if triggered
            else f"{position.stock.ticker} MC ${current_mcap_millions:.0f}M — no action"
        ),
    )


def check_position_too_small(
    position: Position,
    current_value: float,
    portfolio_total: float,
    min_weight: float = 0.03,
    thesis_intact: bool = True,
) -> RebalanceAction:
    """Q2: Has any position fallen below 3% of total portfolio value?

    Top up to 5% minimum if thesis holds, or exit entirely.
    """
    actual_weight = current_value / portfolio_total if portfolio_total > 0 else 0
    triggered = actual_weight < min_weight

    if triggered and thesis_intact:
        action = "TOP_UP_TO_5PCT"
        detail = (
            f"{position.stock.ticker} at {actual_weight:.1%} of portfolio "
            f"(below {min_weight:.0%}) — top up to 5%"
        )
    elif triggered:
        action = "EXIT"
        detail = (
            f"{position.stock.ticker} at {actual_weight:.1%} and thesis broken — exit"
        )
    else:
        action = "HOLD"
        detail = f"{position.stock.ticker} at {actual_weight:.1%} — no action"

    return RebalanceAction(
        question="Q2: Position fallen below 3% of portfolio?",
        triggered=triggered,
        ticker=position.stock.ticker,
        action=action,
        detail=detail,
    )


def check_overconcentration(
    ticker: str,
    current_weight: float,
    max_weight: float = 0.55,
) -> RebalanceAction:
    """Q3: Has monthly DCA created >55% concentration in one name?

    Not automatic trim — flag for conscious decision.
    """
    triggered = current_weight > max_weight
    return RebalanceAction(
        question="Q3: Concentration >55% in single name?",
        triggered=triggered,
        ticker=ticker,
        action="FLAG_FOR_REVIEW" if triggered else "HOLD",
        detail=(
            f"{ticker} at {current_weight:.1%} — exceeds {max_weight:.0%}, "
            f"make conscious decision (not automatic trim)"
            if triggered
            else f"{ticker} at {current_weight:.1%} — below threshold"
        ),
    )


def check_profit_extraction(
    portfolio_value: float,
    cost_basis: float,
    extraction_threshold: float = 10.0,
) -> RebalanceAction:
    """Q4: Is portfolio up >10x from cost basis?

    Remove initial capital entirely. Play with pure profit.
    """
    multiple = portfolio_value / cost_basis if cost_basis > 0 else 0
    triggered = multiple > extraction_threshold
    return RebalanceAction(
        question="Q4: Portfolio up >10x from cost basis?",
        triggered=triggered,
        ticker=None,
        action="EXTRACT_INITIAL_CAPITAL" if triggered else "HOLD",
        detail=(
            f"Portfolio at {multiple:.1f}x cost basis — remove initial "
            f"${cost_basis:.0f}, play with pure profit"
            if triggered
            else f"Portfolio at {multiple:.1f}x cost basis — below {extraction_threshold:.0f}x threshold"
        ),
    )


def run_quarterly_rebalance(
    portfolio: Portfolio,
    current_values: dict[str, float],
    current_mcaps: dict[str, float],
    revenue_growths: dict[str, float],
    thesis_status: dict[str, bool],
) -> list[RebalanceAction]:
    """Run all four quarterly rebalance checks.

    Args:
        portfolio: Current portfolio
        current_values: ticker -> current market value of position
        current_mcaps: ticker -> current market cap in millions
        revenue_growths: ticker -> revenue growth % YoY
        thesis_status: ticker -> True if thesis intact

    Returns:
        List of RebalanceAction results
    """
    actions = []
    total_value = sum(current_values.values()) + portfolio.cash

    for pos in portfolio.positions:
        t = pos.stock.ticker
        val = current_values.get(t, 0)
        mcap = current_mcaps.get(t, 0)
        rev = revenue_growths.get(t, 0)
        thesis = thesis_status.get(t, True)

        # Q1: MC without revenue
        actions.append(check_mcap_without_revenue(pos, mcap, revenue_growth_pct=rev))

        # Q2: Position too small
        actions.append(check_position_too_small(pos, val, total_value, thesis_intact=thesis))

        # Q3: Overconcentration
        weight = val / total_value if total_value > 0 else 0
        actions.append(check_overconcentration(t, weight))

    # Q4: Profit extraction (portfolio-level)
    cost_basis = sum(p.cost_basis for p in portfolio.positions)
    actions.append(check_profit_extraction(total_value, cost_basis))

    return actions
