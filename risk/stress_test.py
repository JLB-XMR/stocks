"""Geopolitical stress test and loss-cutting rules.

Implements the stock-by-stock geopolitical assessment, political calendar
impact analysis, and the explicit loss-cutting decision framework.
"""

from dataclasses import dataclass
from enum import Enum

from data.models import GeopoliticalRisk, Stock


class CutDecision(Enum):
    CUT_IMMEDIATELY = "CUT_IMMEDIATELY"
    CUT_AFTER_QUARTERLY_REVIEW = "CUT_AFTER_QUARTERLY_REVIEW"
    NEVER_CUT_FOR_THIS_REASON = "NEVER_CUT_FOR_THIS_REASON"
    HOLD = "HOLD"


@dataclass
class GeopoliticalAssessment:
    ticker: str
    risk_level: GeopoliticalRisk
    impact: str
    action: str
    is_net_beneficiary: bool


@dataclass
class LossCutResult:
    ticker: str
    decision: CutDecision
    reason: str


# Stock-by-stock geopolitical assessments from the research
GEOPOLITICAL_ASSESSMENTS = [
    GeopoliticalAssessment(
        ticker="ARQQ",
        risk_level=GeopoliticalRisk.LOW,
        impact="Net beneficiary — cyber threats accelerate PQC demand",
        action="Largest position",
        is_net_beneficiary=True,
    ),
    GeopoliticalAssessment(
        ticker="AMSC",
        risk_level=GeopoliticalRisk.LOW,
        impact="Net beneficiary — all scenarios favour grid/defence spending",
        action="Core holding",
        is_net_beneficiary=True,
    ),
    GeopoliticalAssessment(
        ticker="POET",
        risk_level=GeopoliticalRisk.HIGH,
        impact="China manufacturing (Shenzhen) at risk from decoupling/tariffs",
        action="Smaller position, watch May 20 earnings",
        is_net_beneficiary=False,
    ),
    GeopoliticalAssessment(
        ticker="NNOX",
        risk_level=GeopoliticalRisk.SEVERE,
        impact="Israel + Iran war = direct operational risk",
        action="Defer entry until post-earnings; size conservatively",
        is_net_beneficiary=False,
    ),
    GeopoliticalAssessment(
        ticker="VZ",
        risk_level=GeopoliticalRisk.LOW,
        impact="Energy security urgency benefits infrastructure",
        action="Core VCI holding",
        is_net_beneficiary=True,
    ),
    GeopoliticalAssessment(
        ticker="PLAB",
        risk_level=GeopoliticalRisk.MODERATE,
        impact="China revenue exposure in semis downcycle",
        action="Monitor, thesis intact",
        is_net_beneficiary=False,
    ),
]

# Political calendar events
POLITICAL_CALENDAR = [
    {
        "event": "US Mid-terms",
        "date": "November 2026",
        "impact": [
            "Both parties hawkish on China semis → POET pressure increases",
            "Infrastructure spending bipartisan → AMSC benefits regardless",
            "Typically choppy 6 months before, rally 12 months after",
            "Small caps amplify mid-term volatility",
        ],
    },
    {
        "event": "French elections / instability",
        "date": "2026 (ongoing)",
        "impact": [
            "Delays healthcare + defence procurement",
            "Affects NNOX European rollout and ARQQ EU government pipeline",
            "6-12 month timing risk, not thesis-breaker",
        ],
    },
    {
        "event": "Iran war trajectory",
        "date": "Ongoing",
        "impact": [
            "Binary for NNOX — escalation = operational risk; ceasefire = recovery catalyst",
            "Positive for AMSC, VZ (energy security urgency)",
            "Positive for ARQQ (state-sponsored cyber threat premium)",
            "Negative for global risk appetite generally",
        ],
    },
]


# --- Loss-cutting rules ---

# Conditions that trigger immediate cut regardless of price
IMMEDIATE_CUT_TRIGGERS = [
    "Dilution >25% discount or >20% share count increase in one raise",
    "Core regulatory rejection (not delay — hard rejection)",
    "Management fraud or significant governance failure",
    "Technology technically disproved by credible peer-reviewed evidence",
]

# Conditions that trigger cut after one quarterly review
QUARTERLY_REVIEW_CUT_TRIGGERS = [
    "Zero catalysts for 18 months + cash runway under 12 months",
    "Clearly better opportunity has emerged (with written rationale)",
]

# Conditions that should NEVER trigger a cut
NEVER_CUT_TRIGGERS = [
    "Position is down 40, 50, 60%",
    "Broader market crashed",
    "You read a bearish article",
    "It's been flat for 6 months",
    "Someone on social media is negative",
    "You're anxious",
]


def evaluate_loss_cut(
    stock: Stock,
    dilution_discount_pct: float = 0,
    share_count_increase_pct: float = 0,
    regulatory_hard_rejection: bool = False,
    management_fraud: bool = False,
    tech_disproved: bool = False,
    months_without_catalyst: int = 0,
    cash_runway_months: float = float("inf"),
    better_opportunity_exists: bool = False,
    position_down_pct: float = 0,
    market_crashed: bool = False,
) -> LossCutResult:
    """Evaluate whether a position should be cut based on the documented rules.

    Returns a LossCutResult with the decision and reasoning.
    """
    ticker = stock.ticker

    # Immediate cuts
    if dilution_discount_pct > 25 or share_count_increase_pct > 20:
        return LossCutResult(
            ticker, CutDecision.CUT_IMMEDIATELY,
            f"Dilution: {dilution_discount_pct:.0f}% discount / "
            f"{share_count_increase_pct:.0f}% share increase",
        )
    if regulatory_hard_rejection:
        return LossCutResult(
            ticker, CutDecision.CUT_IMMEDIATELY,
            "Core regulatory hard rejection",
        )
    if management_fraud:
        return LossCutResult(
            ticker, CutDecision.CUT_IMMEDIATELY,
            "Management fraud or significant governance failure",
        )
    if tech_disproved:
        return LossCutResult(
            ticker, CutDecision.CUT_IMMEDIATELY,
            "Technology technically disproved by credible evidence",
        )

    # Quarterly review cuts
    if months_without_catalyst >= 18 and cash_runway_months < 12:
        return LossCutResult(
            ticker, CutDecision.CUT_AFTER_QUARTERLY_REVIEW,
            f"No catalysts for {months_without_catalyst} months + "
            f"{cash_runway_months:.0f} month cash runway",
        )
    if better_opportunity_exists:
        return LossCutResult(
            ticker, CutDecision.CUT_AFTER_QUARTERLY_REVIEW,
            "Better opportunity identified (requires written rationale)",
        )

    # Hold — these are NOT reasons to cut
    if position_down_pct > 30 or market_crashed:
        return LossCutResult(
            ticker, CutDecision.NEVER_CUT_FOR_THIS_REASON,
            "Price decline / market crash is NOT a reason to cut. "
            "Ask: 'Would I buy this at today's price?'",
        )

    return LossCutResult(ticker, CutDecision.HOLD, "No cut triggers active")


def the_one_rule(would_buy_at_current_price: bool) -> str:
    """The One Rule That Covers Everything:
    'If I didn't own this and had fresh cash today, would I buy it at this price?'

    Yes -> Hold or add
    No  -> Ask why. Price reason (doesn't matter) or thesis reason (does matter)
    """
    if would_buy_at_current_price:
        return "YES → Hold or add"
    return "NO → Investigate: Is it a price reason (ignore) or thesis reason (act)?"
