"""Telegram notification and approval gate.

Sends rebalance proposals to Telegram and waits for YES/NO approval.
Includes /stop command to halt the bot.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from bot.engine import RebalanceResult, Trade

logger = logging.getLogger(__name__)


@dataclass
class ApprovalResult:
    approved: bool
    responded_by: str
    response_time_seconds: float


def format_rebalance_message(result: RebalanceResult) -> str:
    """Format a rebalance proposal for Telegram."""
    lines = [
        "📊 *VCI Rebalance Proposal*",
        f"Max drift: {result.max_drift:.1%}",
        "",
        "*Proposed Trades:*",
    ]

    for trade in result.trades:
        emoji = "🟢" if trade.action == "BUY" else "🔴"
        lines.append(
            f"{emoji} {trade.action} {trade.shares} {trade.ticker} "
            f"(~${trade.estimated_value:.0f}) — {trade.reason}"
        )

    lines.extend([
        "",
        "*Drifts:*",
    ])
    for ticker, drift in sorted(result.drifts.items(), key=lambda x: abs(x[1]), reverse=True):
        if abs(drift) > 0.005:
            direction = "↑" if drift > 0 else "↓"
            lines.append(f"  {ticker}: {direction} {abs(drift):.1%}")

    lines.extend([
        "",
        "Reply *YES* to execute or *NO* to cancel.",
        "Timeout: 4 hours.",
    ])

    return "\n".join(lines)


def format_trade_confirmation(trades: list[Trade], dry_run: bool) -> str:
    """Format trade execution confirmation."""
    mode = "🧪 DRY RUN" if dry_run else "✅ LIVE"
    lines = [f"{mode} *Trades Executed:*", ""]

    for trade in trades:
        lines.append(f"• {trade.action} {trade.shares} {trade.ticker} (~${trade.estimated_value:.0f})")

    return "\n".join(lines)


def format_kill_switch_alert(loss_pct: float) -> str:
    """Format kill switch activation alert."""
    return (
        f"🚨 *KILL SWITCH ACTIVATED*\n\n"
        f"Daily loss: {loss_pct:.1%}\n"
        f"All trading halted. Manual restart required.\n\n"
        f"Send /start to resume after investigation."
    )


class TelegramNotifier:
    """Telegram bot for notifications and trade approval.

    Requires python-telegram-bot and a bot token from @BotFather.
    """

    def __init__(self, bot_token: str, chat_id: str, approval_timeout: int = 14400):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.approval_timeout = approval_timeout  # 4 hours default
        self._bot = None
        self._stopped = False

    async def initialize(self) -> None:
        """Initialize the Telegram bot."""
        try:
            from telegram import Bot
            self._bot = Bot(token=self.bot_token)
            logger.info("Telegram bot initialized")
        except ImportError:
            raise RuntimeError(
                "python-telegram-bot required. Install with: pip install python-telegram-bot"
            )

    async def send_message(self, text: str) -> None:
        """Send a message to the configured chat."""
        if not self._bot:
            logger.warning("Telegram bot not initialized — logging message instead")
            logger.info("Telegram message: %s", text)
            return

        await self._bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode="Markdown",
        )

    async def request_approval(self, result: RebalanceResult) -> ApprovalResult:
        """Send rebalance proposal and wait for YES/NO response.

        Returns ApprovalResult. Times out after approval_timeout seconds.
        """
        message = format_rebalance_message(result)
        await self.send_message(message)

        logger.info(
            "Approval requested — waiting up to %d seconds",
            self.approval_timeout,
        )

        # In production, this would poll for updates or use a webhook.
        # Simplified: wait for manual response via separate polling mechanism.
        # The actual implementation would use telegram.ext.Application with handlers.
        logger.info(
            "NOTE: Full approval gate requires telegram.ext.Application with "
            "MessageHandler. This scaffold logs the proposal and proceeds in dry-run."
        )

        return ApprovalResult(
            approved=False,
            responded_by="TIMEOUT",
            response_time_seconds=0,
        )

    @property
    def is_stopped(self) -> bool:
        return self._stopped

    def stop(self) -> None:
        """Handle /stop command."""
        self._stopped = True
        logger.critical("Bot stopped via /stop command")

    def start(self) -> None:
        """Handle /start command to resume after kill switch."""
        self._stopped = False
        logger.info("Bot resumed via /start command")
