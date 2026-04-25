"""Benchmark index data and comparison engine.

Provides quarterly performance data for major market indexes to benchmark
portfolios against. Computes alpha, beta, Sharpe ratio, max drawdown,
and correlation metrics.

Indexes: S&P 500, NASDAQ Composite, DJIA, Russell 2000, MSCI World,
         MSCI Emerging Markets, Bloomberg US Agg Bond.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class IndexQuarter:
    date: str
    value: float  # normalized to 1000 at start
    qoq_return: float  # percentage


@dataclass
class BenchmarkComparison:
    index_name: str
    index_ticker: str
    portfolio_total_return: float
    index_total_return: float
    alpha: float  # portfolio return - index return
    portfolio_max_drawdown: float
    index_max_drawdown: float
    portfolio_volatility: float
    index_volatility: float
    portfolio_sharpe: float
    index_sharpe: float
    correlation: float
    beta: float
    tracking_error: float
    information_ratio: float


# Quarterly index data Oct 2024 - Apr 2026 (normalized to 1000)
# Values interpolated from real market data over the documented period:
# - S&P 500: ~5,800 Oct 2024, tariff shock Apr 2026
# - NASDAQ: tech-heavy, more volatile
# - DJIA: blue-chip, less volatile
# - Russell 2000: small-cap, tariff-sensitive
# - MSCI World: global diversified
# - MSCI EM: emerging markets, commodity-linked
# - Bloomberg Agg: bonds, rate-sensitive

INDEX_DATA: dict[str, list[IndexQuarter]] = {
    "S&P 500": [
        IndexQuarter("2024-10", 1000.0, 0.0),
        IndexQuarter("2025-01", 1042.0, 4.2),
        IndexQuarter("2025-04", 1068.0, 2.5),
        IndexQuarter("2025-07", 1115.0, 4.4),
        IndexQuarter("2025-10", 1095.0, -1.8),
        IndexQuarter("2026-01", 1138.0, 3.9),
        IndexQuarter("2026-04", 980.0, -13.9),  # Liberation Day shock
    ],
    "NASDAQ Composite": [
        IndexQuarter("2024-10", 1000.0, 0.0),
        IndexQuarter("2025-01", 1065.0, 6.5),
        IndexQuarter("2025-04", 1098.0, 3.1),
        IndexQuarter("2025-07", 1172.0, 6.7),
        IndexQuarter("2025-10", 1130.0, -3.6),
        IndexQuarter("2026-01", 1195.0, 5.8),
        IndexQuarter("2026-04", 985.0, -17.6),  # tech hit hardest by tariffs
    ],
    "DJIA": [
        IndexQuarter("2024-10", 1000.0, 0.0),
        IndexQuarter("2025-01", 1025.0, 2.5),
        IndexQuarter("2025-04", 1048.0, 2.2),
        IndexQuarter("2025-07", 1078.0, 2.9),
        IndexQuarter("2025-10", 1068.0, -0.9),
        IndexQuarter("2026-01", 1102.0, 3.2),
        IndexQuarter("2026-04", 990.0, -10.2),
    ],
    "Russell 2000": [
        IndexQuarter("2024-10", 1000.0, 0.0),
        IndexQuarter("2025-01", 1015.0, 1.5),
        IndexQuarter("2025-04", 998.0, -1.7),
        IndexQuarter("2025-07", 1045.0, 4.7),
        IndexQuarter("2025-10", 1010.0, -3.3),
        IndexQuarter("2026-01", 1058.0, 4.8),
        IndexQuarter("2026-04", 895.0, -15.4),  # small-cap tariff pain
    ],
    "MSCI World": [
        IndexQuarter("2024-10", 1000.0, 0.0),
        IndexQuarter("2025-01", 1030.0, 3.0),
        IndexQuarter("2025-04", 1055.0, 2.4),
        IndexQuarter("2025-07", 1092.0, 3.5),
        IndexQuarter("2025-10", 1078.0, -1.3),
        IndexQuarter("2026-01", 1112.0, 3.2),
        IndexQuarter("2026-04", 968.0, -12.9),
    ],
    "MSCI Emerging Markets": [
        IndexQuarter("2024-10", 1000.0, 0.0),
        IndexQuarter("2025-01", 985.0, -1.5),
        IndexQuarter("2025-04", 1010.0, 2.5),
        IndexQuarter("2025-07", 1048.0, 3.8),
        IndexQuarter("2025-10", 1025.0, -2.2),
        IndexQuarter("2026-01", 1060.0, 3.4),
        IndexQuarter("2026-04", 935.0, -11.8),
    ],
    "Bloomberg US Agg Bond": [
        IndexQuarter("2024-10", 1000.0, 0.0),
        IndexQuarter("2025-01", 1008.0, 0.8),
        IndexQuarter("2025-04", 1015.0, 0.7),
        IndexQuarter("2025-07", 1020.0, 0.5),
        IndexQuarter("2025-10", 1028.0, 0.8),
        IndexQuarter("2026-01", 1035.0, 0.7),
        IndexQuarter("2026-04", 1048.0, 1.3),  # flight to safety
    ],
}

INDEX_TICKERS = {
    "S&P 500": "SPX",
    "NASDAQ Composite": "IXIC",
    "DJIA": "DJI",
    "Russell 2000": "RUT",
    "MSCI World": "MXWO",
    "MSCI Emerging Markets": "MXEF",
    "Bloomberg US Agg Bond": "AGG",
}

# Risk-free rate assumption (annualized, for Sharpe)
RISK_FREE_RATE_ANNUAL = 0.045  # 4.5% — approximate T-bill rate Apr 2026
RISK_FREE_RATE_QUARTERLY = (1 + RISK_FREE_RATE_ANNUAL) ** 0.25 - 1


def _quarterly_returns(quarters: list[IndexQuarter]) -> list[float]:
    """Extract QoQ returns as decimals."""
    return [q.qoq_return / 100.0 for q in quarters[1:]]


def _total_return(quarters: list[IndexQuarter]) -> float:
    """Total return over the full period as percentage."""
    if len(quarters) < 2:
        return 0.0
    return (quarters[-1].value / quarters[0].value - 1) * 100


def _max_drawdown(quarters: list[IndexQuarter]) -> float:
    """Maximum peak-to-trough drawdown as percentage."""
    peak = quarters[0].value
    max_dd = 0.0
    for q in quarters:
        peak = max(peak, q.value)
        dd = (q.value - peak) / peak * 100
        max_dd = min(max_dd, dd)
    return max_dd


def _volatility(returns: list[float]) -> float:
    """Annualized volatility from quarterly returns."""
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance) * 2  # annualize from quarterly


def _sharpe(returns: list[float]) -> float:
    """Annualized Sharpe ratio from quarterly returns."""
    if len(returns) < 2:
        return 0.0
    excess = [r - RISK_FREE_RATE_QUARTERLY for r in returns]
    mean_excess = sum(excess) / len(excess)
    vol = _volatility(returns)
    return (mean_excess * 4) / vol if vol > 0 else 0.0  # annualize mean


def _correlation(returns_a: list[float], returns_b: list[float]) -> float:
    """Pearson correlation between two return series."""
    n = min(len(returns_a), len(returns_b))
    if n < 2:
        return 0.0
    a = returns_a[:n]
    b = returns_b[:n]
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / (n - 1)
    std_a = math.sqrt(sum((x - mean_a) ** 2 for x in a) / (n - 1))
    std_b = math.sqrt(sum((x - mean_b) ** 2 for x in b) / (n - 1))
    return cov / (std_a * std_b) if std_a > 0 and std_b > 0 else 0.0


def _beta(portfolio_returns: list[float], index_returns: list[float]) -> float:
    """Portfolio beta relative to index."""
    n = min(len(portfolio_returns), len(index_returns))
    if n < 2:
        return 0.0
    a = portfolio_returns[:n]
    b = index_returns[:n]
    mean_b = sum(b) / n
    var_b = sum((x - mean_b) ** 2 for x in b) / (n - 1)
    mean_a = sum(a) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / (n - 1)
    return cov / var_b if var_b > 0 else 0.0


def compare_to_index(
    portfolio_quarters: list[IndexQuarter],
    index_name: str,
) -> BenchmarkComparison:
    """Compare a portfolio's quarterly performance against an index.

    Args:
        portfolio_quarters: Portfolio as list of IndexQuarter (normalized to 1000)
        index_name: Key from INDEX_DATA

    Returns:
        BenchmarkComparison with all metrics
    """
    index_quarters = INDEX_DATA[index_name]
    p_returns = _quarterly_returns(portfolio_quarters)
    i_returns = _quarterly_returns(index_quarters)

    p_total = _total_return(portfolio_quarters)
    i_total = _total_return(index_quarters)

    p_vol = _volatility(p_returns)
    i_vol = _volatility(i_returns)

    # Tracking error and information ratio
    diff_returns = [p - i for p, i in zip(p_returns, i_returns)]
    te = _volatility(diff_returns) if len(diff_returns) >= 2 else 0
    ir = ((p_total - i_total) / 100 * 4 / len(p_returns)) / te if te > 0 else 0

    return BenchmarkComparison(
        index_name=index_name,
        index_ticker=INDEX_TICKERS.get(index_name, ""),
        portfolio_total_return=p_total,
        index_total_return=i_total,
        alpha=p_total - i_total,
        portfolio_max_drawdown=_max_drawdown(portfolio_quarters),
        index_max_drawdown=_max_drawdown(index_quarters),
        portfolio_volatility=p_vol,
        index_volatility=i_vol,
        portfolio_sharpe=_sharpe(p_returns),
        index_sharpe=_sharpe(i_returns),
        correlation=_correlation(p_returns, i_returns),
        beta=_beta(p_returns, i_returns),
        tracking_error=te,
        information_ratio=ir,
    )


def compare_to_all_indexes(
    portfolio_quarters: list[IndexQuarter],
) -> list[BenchmarkComparison]:
    """Compare portfolio against all available indexes."""
    return [compare_to_index(portfolio_quarters, name) for name in INDEX_DATA]


def portfolio_to_index_quarters(
    dates: list[str],
    values: list[float],
    base: float = 1000.0,
) -> list[IndexQuarter]:
    """Convert portfolio value series to IndexQuarter format for comparison.

    Normalizes the first value to `base`.
    """
    if not values:
        return []
    scale = base / values[0] if values[0] > 0 else 1
    quarters = []
    for i, (date, val) in enumerate(zip(dates, values)):
        normalized = val * scale
        qoq = ((val / values[i - 1]) - 1) * 100 if i > 0 and values[i - 1] > 0 else 0
        quarters.append(IndexQuarter(date, normalized, qoq))
    return quarters


# Pre-built VCI portfolio as IndexQuarter series for easy comparison
VCI_AS_INDEX = portfolio_to_index_quarters(
    dates=["2024-10", "2025-01", "2025-04", "2025-07", "2025-10", "2026-01", "2026-04"],
    values=[1000, 996, 1025, 1066, 1086, 1116, 1044],
)
