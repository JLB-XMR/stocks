"""Core data models for the investment portfolio analysis system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Sector(Enum):
    ENERGY = "Energy"
    AUTOS = "Autos"
    TELECOMS = "Telecoms"
    FINANCIALS = "Financials"
    HEALTHCARE = "Healthcare"
    SEMICONDUCTORS = "Semiconductors"
    INDUSTRIALS = "Industrials"
    AGRITECH = "AgriTech"
    SPATIAL = "Spatial"
    CYBERSECURITY = "Cybersecurity"
    PHOTONICS = "Photonics"
    MEDICAL_DEVICES = "Medical Devices"
    NUCLEAR = "Nuclear"
    OTHER = "Other"


class DebtLevel(Enum):
    NONE = "None"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


class GeopoliticalRisk(Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    SEVERE = "Severe"


class PortfolioTier(Enum):
    VCI_VALUE = "VCI Value"
    VCI_BRIDGE = "VCI/Bridge"
    MOONSHOT = "Moonshot"
    BRIDGE = "Bridge"
    CASH = "Cash"


@dataclass
class Stock:
    ticker: str
    name: str
    sector: Sector
    ttm_pe: Optional[float]  # None for loss-making companies
    forward_pe: Optional[float]
    debt_level: DebtLevel
    market_cap_millions: float
    price: float  # as of Apr 2-4, 2026
    week52_low: float
    week52_high: float
    geopolitical_risk: GeopoliticalRisk
    ai_thesis: str
    kill_triggers: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Position:
    stock: Stock
    shares: float
    entry_price: float
    cost_basis: float
    weight: float  # target weight as decimal (0.10 = 10%)
    tier: PortfolioTier


@dataclass
class Portfolio:
    name: str
    positions: list[Position]
    cash: float
    total_value: float
    currency: str = "USD"
    description: str = ""


@dataclass
class BacktestQuarter:
    date: str
    portfolio_value: float
    qoq_change: float  # percentage
    key_driver: str


@dataclass
class BacktestResult:
    total_return: float
    peak_value: float
    trough_value: float
    max_drawdown: float
    benchmark_return: float
    quarters: list[BacktestQuarter]
    winners: dict[str, float]  # ticker -> return %
    detractors: dict[str, float]


@dataclass
class ReturnScenario:
    name: str  # Bull, Base, Bear
    multipliers: dict[str, float]  # ticker -> multiplier
    portfolio_multiple: float
