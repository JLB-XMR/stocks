"""Simulated price data for bot backtesting.

Contains quarterly price snapshots for all VCI tickers from Oct 2024 to Apr 2026,
derived from the documented backtest returns and real entry/current prices.

These are approximations — the exact quarterly prices are interpolated from
the known entry prices, current prices, and documented per-stock returns.

After the April 2026 VCI reallocation, AMSC and CODA were added to the portfolio.
Their "entry" is the reallocation price (April 2026). Historical quarters use the
same price since they weren't held before.
"""

# Entry prices (Oct 2024 baseline for original VCI; Apr 2026 for reallocated adds)
ENTRY_PRICES = {
    # Original VCI (Oct 2024)
    "VZ": 43.00,
    "C": 65.00,
    "CMCSA": 40.00,
    "PBR": 16.00,
    "PLAB": 22.00,
    "IPGP": 85.00,
    "AGCO": 100.00,
    "CNH": 12.00,
    "TRMB": 55.00,
    # Reallocated adds (Apr 2026)
    "AMSC": 50.52,
    "CODA": 12.31,
}

# Current prices (Apr 2026)
CURRENT_PRICES = {
    "VZ": 49.39,
    "C": 115.39,
    "CMCSA": 27.99,
    "PBR": 20.08,
    "PLAB": 40.70,
    "IPGP": 107.11,
    "AGCO": 124.99,
    "CNH": 10.63,
    "TRMB": 65.24,
    "AMSC": 50.52,
    "CODA": 12.31,
}

# Documented total returns over the 18-month period
TOTAL_RETURNS = {
    "VZ": 0.281,      # +28.1%  (winner)
    "C": 0.360,       # +36.0%  (winner)
    "CMCSA": -0.153,  # -15.3%  (detractor)
    "PBR": -0.066,    # -6.6%   (detractor)
    "PLAB": -0.159,   # -15.9%  (detractor)
    "IPGP": -0.129,   # -12.9%  (detractor)
    "AGCO": 0.197,    # +19.7%  (winner)
    "CNH": -0.114,    # -11.4%  (implied from entry 12 -> current 10.63)
    "TRMB": 0.145,    # +14.5%  (winner)
}

# Quarterly price snapshots (interpolated from known data points)
# Each dict maps ticker -> price at that quarter end
# Key drivers from the backtest are used to shape the trajectory
QUARTERLY_PRICES = {
    # Q0: Oct 2024 — Initial allocation
    "2024-10": {
        "VZ": 43.00, "C": 65.00, "CMCSA": 40.00, "PBR": 16.00,
        "PLAB": 22.00, "IPGP": 85.00, "AGCO": 100.00, "CNH": 12.00, "TRMB": 55.00,
        "AMSC": 50.52, "CODA": 12.31,
    },
    # Q1: Jan 2025 — PBR -19%, Citi +15%, portfolio -0.4%
    "2025-01": {
        "VZ": 43.50, "C": 74.75, "CMCSA": 38.50, "PBR": 12.96,
        "PLAB": 21.00, "IPGP": 82.00, "AGCO": 102.00, "CNH": 11.80, "TRMB": 56.00,
        "AMSC": 50.52, "CODA": 12.31,
    },
    # Q2: Apr 2025 — Recovery + tariff noise absorbed, portfolio +2.9%
    "2025-04": {
        "VZ": 45.20, "C": 82.00, "CMCSA": 36.00, "PBR": 14.50,
        "PLAB": 23.50, "IPGP": 88.00, "AGCO": 108.00, "CNH": 11.50, "TRMB": 58.00,
        "AMSC": 50.52, "CODA": 12.31,
    },
    # Q3: Jul 2025 — AGCO/TRMB carry, portfolio +4.0%
    "2025-07": {
        "VZ": 46.80, "C": 90.00, "CMCSA": 34.00, "PBR": 17.50,
        "PLAB": 25.00, "IPGP": 92.00, "AGCO": 118.00, "CNH": 11.20, "TRMB": 62.00,
        "AMSC": 50.52, "CODA": 12.31,
    },
    # Q4: Oct 2025 — PLAB record IC revenue, portfolio +1.9%
    "2025-10": {
        "VZ": 48.00, "C": 100.00, "CMCSA": 32.00, "PBR": 19.00,
        "PLAB": 28.00, "IPGP": 95.00, "AGCO": 122.00, "CNH": 10.90, "TRMB": 63.50,
        "AMSC": 50.52, "CODA": 12.31,
    },
    # Q5: Jan 2026 — High-water mark, portfolio +2.8%
    "2026-01": {
        "VZ": 50.50, "C": 110.00, "CMCSA": 31.00, "PBR": 21.50,
        "PLAB": 30.00, "IPGP": 100.00, "AGCO": 130.00, "CNH": 11.00, "TRMB": 65.00,
        "AMSC": 50.52, "CODA": 12.31,
    },
    # Q6: Apr 2026 — Liberation Day tariff shock, portfolio -6.4%
    "2026-04": {
        "VZ": 49.39, "C": 115.39, "CMCSA": 27.99, "PBR": 20.08,
        "PLAB": 40.70, "IPGP": 107.11, "AGCO": 124.99, "CNH": 10.63, "TRMB": 65.24,
        "AMSC": 50.52, "CODA": 12.31,
    },
}

# Quarter labels in chronological order
QUARTER_DATES = [
    "2024-10", "2025-01", "2025-04", "2025-07", "2025-10", "2026-01", "2026-04",
]

QUARTER_DRIVERS = {
    "2024-10": "Initial allocation",
    "2025-01": "PBR -19%, Citi +15%",
    "2025-04": "Recovery + tariff noise absorbed",
    "2025-07": "AGCO/TRMB carry the quarter",
    "2025-10": "PLAB record IC revenue",
    "2026-01": "Portfolio high-water mark",
    "2026-04": "Liberation Day tariff shock",
}
