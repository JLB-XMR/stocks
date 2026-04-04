# stocks
Investment portfolio analysis and automated rebalancing system.

## Portfolios

### Portfolio 1 — Value Convergence Index (VCI)
9 stocks + 10% cash. EUR 1,000 base. Quarterly rebalancing.

**Thesis:** Cheap entry on unglamorous, cash-generating businesses that become critical infrastructure as AI, energy transition, and food security converge — priced as if none of that transformation happens.

Holdings: VZ, C, CMCSA, PBR, PLAB, IPGP, AGCO, CNH, TRMB

### Portfolio 2 — $1,500 Moonshot
Target 50-75x over 5-7 years. Three tiers: moonshots, bridge, cash.

Holdings: ARQQ (41%), POET (22%), NNOX (10%), AMSC (9%), PLAB (8%), Cash (10%)

## Usage

```bash
pip install -r requirements.txt

# Portfolio summaries
python analyze.py portfolio vci
python analyze.py portfolio moonshot

# VCI 18-month backtest (Oct 2024 - Apr 2026)
python analyze.py backtest

# Moonshot return scenarios (Bull/Base/Bear)
python analyze.py scenarios

# DCA decision tree
python analyze.py dca

# Geopolitical risk assessment
python analyze.py risk          # all stocks
python analyze.py risk ARQQ     # single stock

# Full stock universe
python analyze.py universe
```

## IBKR Rebalancing Bot

Automated quarterly rebalancing for the VCI portfolio via Interactive Brokers Gateway.

```bash
cp .env.example .env   # fill in your secrets
python -m bot.main --once   # single check
python -m bot.main          # scheduled (weekdays 9:30 AM)
```

### Guardrails
- Position size cap: no single order >15% of portfolio
- Daily loss limit: kill switch at -3%
- Market hours check: never trades outside regular hours
- DRY_RUN=true by default
- Limit orders only — never market orders
- Telegram approval gate with 4-hour timeout

## Project Structure

```
stocks/
├── analyze.py              # CLI entry point
├── data/
│   ├── models.py           # Core data models
│   └── stocks.py           # Stock universe (16 stocks)
├── portfolios/
│   ├── vci.py              # VCI portfolio definition
│   └── moonshot.py         # Moonshot portfolio definition
├── backtest/
│   └── engine.py           # Backtest + forward simulation
├── rebalance/
│   ├── dca.py              # DCA decision tree
│   └── quarterly.py        # Quarterly rebalance rules
├── risk/
│   └── stress_test.py      # Geopolitical + loss-cutting rules
├── bot/
│   ├── config.py           # Bot configuration
│   ├── connector.py        # IBKR Gateway connector
│   ├── engine.py           # Drift calculator + trade generator
│   ├── executor.py         # Order executor + SQLite logger
│   ├── notifier.py         # Telegram notifications
│   └── main.py             # Bot scheduler
├── .env.example
├── .gitignore
└── requirements.txt
```
