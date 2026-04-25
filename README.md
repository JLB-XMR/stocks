# stocks
Investment portfolio analysis and automated rebalancing system.

## Portfolios

### Portfolio — VCI Reallocated (April 2026)
7 positions + 13% cash. Quarterly rebalancing. EUR 800/month DCA.

**Thesis:** Cheap entry on unglamorous, cash-generating businesses that become critical infrastructure as AI, energy transition, and food security converge — priced as if none of that transformation happens.

Holdings: AMSC (17%), VZ (13%), CNH (13%), CMCSA (13%), PLAB (12%), PBR (11%), CODA (8%), Cash (13%)

### Original Portfolios (Historical)
- **VCI (Oct 2024):** VZ, C, CMCSA, PBR, PLAB, IPGP, AGCO, CNH, TRMB — EUR 1,000 base
- **Moonshot:** ARQQ 41%, POET 22%, NNOX 10%, AMSC 9%, PLAB 8%, Cash 10% — $1,500 base

## Usage

```bash
pip install -r requirements.txt

# Portfolio summaries
python analyze.py portfolio vci
python analyze.py portfolio moonshot

# VCI 18-month backtest (Oct 2024 - Apr 2026)
python analyze.py backtest

# Backtest with benchmark comparison (7 indexes)
python analyze.py backtest-bench

# Moonshot return scenarios (Bull/Base/Bear)
python analyze.py scenarios

# DCA decision tree
python analyze.py dca

# Geopolitical risk assessment
python analyze.py risk          # all stocks
python analyze.py risk ARQQ     # single stock

# Full stock universe
python analyze.py universe

# VCI reallocation plan (rebuild IBKR portfolio with VCI thesis)
python analyze.py reallocate

# Compare thesis vs actual IBKR portfolio
python analyze.py compare

# Google Sheets dashboard
python analyze.py dashboard --credentials key.json --share you@email.com
python analyze.py dashboard --credentials key.json --update SPREADSHEET_ID
```

## Benchmark Comparison

Compares VCI portfolio against 7 major indexes:

| Index | Ticker | What it measures |
|-------|--------|-----------------|
| S&P 500 | SPX | US large-cap |
| NASDAQ Composite | IXIC | US tech-heavy |
| DJIA | DJI | US blue-chip |
| Russell 2000 | RUT | US small-cap |
| MSCI World | MXWO | Global developed |
| MSCI Emerging Markets | MXEF | Emerging markets |
| Bloomberg US Agg Bond | AGG | US investment-grade bonds |

Metrics computed: alpha, beta, Sharpe ratio, max drawdown, volatility, correlation, tracking error, information ratio.

```bash
python analyze.py backtest-bench
```

## Google Sheets Dashboard

Creates a 6-sheet dashboard:
1. **Portfolio Overview** — Both portfolios with positions, weights, returns
2. **Benchmark Comparison** — VCI vs all 7 indexes with full metrics
3. **Quarterly Performance** — Quarter-by-quarter VCI vs all indexes
4. **Risk Dashboard** — Geopolitical assessments, political calendar, loss-cutting rules
5. **Moonshot Scenarios** — Bull/Base/Bear projections with ETAs
6. **Stock Universe** — All 16 stocks with thesis and metadata

### Setup
1. Create a Google Cloud project, enable the Sheets API
2. Create a service account, download the JSON key
3. Add `GOOGLE_SHEETS_CREDENTIALS=/path/to/key.json` to `.env`
4. Run `python analyze.py dashboard --credentials key.json --share you@email.com`

## Claude Code Agents

Three custom agents in `.claude/agents/` for use as subagents:

| Agent | What it does |
|-------|-------------|
| `backtest-runner` | Replays historical quarters, runs forward simulations, benchmarks against all 7 indexes |
| `risk-checker` | Evaluates stocks against loss-cutting rules, geopolitical stress tests, risk benchmarks vs indexes |
| `portfolio-tracker` | Tracks portfolio state, DCA decisions, rebalancing, creates/updates Google Sheets dashboard |

All three can benchmark against indexes and export to Google Sheets.

## Bot Simulation (Accelerated Paper Trading)

Validate the full bot pipeline locally without waiting for real market sessions.

```bash
# Full suite: historical replay + stress tests
python analyze.py simulate

# Guardrail stress tests only (9 tests)
python analyze.py simulate stress

# Synthetic drift scenarios (mild, heavy, crash, moonshot)
python analyze.py simulate synthetic

# Or run directly
python -m bot.simulator              # all
python -m bot.simulator --stress     # guardrails only
python -m bot.simulator --synthetic crash   # single scenario
python -m bot.simulator --all-synthetic     # all scenarios
```

### What it tests
- **Historical replay**: 6 quarters (Oct '24 - Apr '26) through drift/trade pipeline
- **Synthetic drift**: Injects artificial price moves to trigger every code path
  - `mild`: modest divergence, just above 5% threshold
  - `heavy`: one position +80%, another -40%
  - `crash`: broad 15-25% selloff (should NOT rebalance — weights unchanged)
  - `moonshot`: one position 5x breakout (tests position cap + redistribution)
- **Guardrail stress tests** (9 tests):
  - Kill switch triggers at -3%, doesn't false-trigger at -2%
  - Position size cap enforced at 15%
  - Empty portfolio handled gracefully
  - Missing tickers detected
  - SQLite logging verified
  - Message formatting for all scenarios

### Recommended workflow
1. Run `python analyze.py simulate` — all 9 tests must pass
2. Connect to IBKR paper account, run `python -m bot.main --once`
3. Verify 2-3 live paper sessions over 2-3 days
4. Switch to live with `DRY_RUN=false`

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
├── analyze.py              # CLI entry point (12 commands)
├── data/
│   ├── models.py           # Core data models
│   └── stocks.py           # Stock universe (16 stocks)
├── portfolios/
│   ├── vci.py              # VCI portfolio definition
│   └── moonshot.py         # Moonshot portfolio definition
├── backtest/
│   ├── engine.py           # Backtest + forward simulation
│   ├── benchmarks.py       # 7 index benchmarks + comparison metrics
│   └── comparison.py       # Thesis vs actual IBKR comparison
├── rebalance/
│   ├── dca.py              # DCA decision tree
│   ├── quarterly.py        # Quarterly rebalance rules
│   └── vci_reallocate.py   # VCI reallocation engine
├── risk/
│   └── stress_test.py      # Geopolitical + loss-cutting rules
├── dashboard/
│   └── sheets.py           # Google Sheets dashboard (6 sheets)
├── bot/
│   ├── config.py           # Bot configuration
│   ├── connector.py        # IBKR Gateway connector
│   ├── engine.py           # Drift calculator + trade generator
│   ├── executor.py         # Order executor + SQLite logger
│   ├── notifier.py         # Telegram notifications
│   ├── main.py             # Bot scheduler
│   ├── simulator.py        # Historical replay + stress tests
│   └── sim_data.py         # Quarterly price snapshots
├── .claude/agents/
│   ├── backtest-runner.md  # Backtest agent definition
│   ├── risk-checker.md     # Risk checker agent definition
│   └── portfolio-tracker.md # Portfolio tracker agent definition
├── .env.example
├── .gitignore
└── requirements.txt
```
