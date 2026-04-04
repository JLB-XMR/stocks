"""Main bot scheduler.

Runs weekdays at 9:30 AM EST. Triggers rebalance if:
- Drift >5% on any position, OR
- First trading day of the quarter (Jan, Apr, Jul, Oct)

Usage:
    python -m bot.main          # Run scheduler
    python -m bot.main --once   # Run once and exit
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime

import schedule

from bot.config import BotConfig
from bot.connector import IBKRConnector
from bot.engine import calculate_drift
from bot.executor import OrderExecutor
from bot.notifier import TelegramNotifier, format_kill_switch_alert, format_trade_confirmation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def is_first_trading_day_of_quarter() -> bool:
    """Check if today is the first trading day of a quarter month."""
    today = datetime.now()
    if today.month not in (1, 4, 7, 10):
        return False
    # First weekday of the month
    if today.day <= 3 and today.weekday() < 5:
        return True
    return False


async def run_rebalance_check(config: BotConfig) -> None:
    """Core rebalance check logic."""
    connector = IBKRConnector(config.ibkr_host, config.ibkr_port, config.ibkr_client_id)
    executor = OrderExecutor(config)
    notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)

    try:
        await connector.connect()
        await notifier.initialize()

        if notifier.is_stopped:
            logger.info("Bot is stopped. Send /start to resume.")
            return

        # Get current portfolio state
        snapshot = await connector.get_portfolio_snapshot()
        logger.info(
            "Portfolio: $%.0f total, $%.0f cash, %d positions",
            snapshot.total_value, snapshot.cash, len(snapshot.positions),
        )

        # Check daily loss limit
        if executor.check_daily_loss_limit(snapshot.total_value, snapshot.total_value):
            await notifier.send_message(format_kill_switch_alert(0))
            return

        # Calculate drift
        result = calculate_drift(snapshot, config)
        logger.info("Max drift: %.1f%%, needs rebalance: %s",
                     result.max_drift * 100, result.needs_rebalance)

        force_rebalance = is_first_trading_day_of_quarter()
        if force_rebalance:
            logger.info("First trading day of quarter — forcing rebalance check")

        if not result.needs_rebalance and not force_rebalance:
            logger.info("No rebalance needed. Max drift: %.1f%%", result.max_drift * 100)
            return

        # Request approval via Telegram
        approval = await notifier.request_approval(result)

        if config.dry_run:
            logger.info("DRY RUN mode — executing without approval")
            results = await executor.execute_trades(result.trades)
            await notifier.send_message(format_trade_confirmation(result.trades, dry_run=True))
        elif approval.approved:
            await executor.connect()
            results = await executor.execute_trades(result.trades)
            await notifier.send_message(format_trade_confirmation(result.trades, dry_run=False))
        else:
            logger.info("Rebalance not approved (response: %s)", approval.responded_by)
            await notifier.send_message("❌ Rebalance cancelled.")

    except ConnectionError as e:
        logger.error("Connection error: %s", e)
        await notifier.send_message(f"⚠️ Connection error: {e}")
    finally:
        await connector.disconnect()


def run_scheduled() -> None:
    """Wrapper for schedule library (sync)."""
    config = BotConfig.from_env()
    asyncio.run(run_rebalance_check(config))


def main() -> None:
    parser = argparse.ArgumentParser(description="VCI Portfolio Rebalancing Bot")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    config = BotConfig.from_env()

    if args.once:
        logger.info("Running single rebalance check...")
        asyncio.run(run_rebalance_check(config))
        return

    # Schedule weekday checks at 9:30 AM
    schedule.every().monday.at(config.rebalance_time).do(run_scheduled)
    schedule.every().tuesday.at(config.rebalance_time).do(run_scheduled)
    schedule.every().wednesday.at(config.rebalance_time).do(run_scheduled)
    schedule.every().thursday.at(config.rebalance_time).do(run_scheduled)
    schedule.every().friday.at(config.rebalance_time).do(run_scheduled)

    logger.info("VCI Bot started. Checking weekdays at %s", config.rebalance_time)
    logger.info("DRY_RUN=%s", config.dry_run)

    while True:
        schedule.run_pending()
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(30))


if __name__ == "__main__":
    main()
