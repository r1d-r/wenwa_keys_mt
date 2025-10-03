"""
Partial Take Profit (PTP) trigger system.
Monitors positions and automatically closes partial profits when trigger prices are hit.
"""

import json
import os
import threading
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from src.config.logger import get_logger
from src.mt5_manager.connection import get_connection
from src.mt5_manager.positions import get_position_manager
from src.mt5_manager.trading import get_trading_manager
from src.mt5_manager.utils import get_current_bid, get_current_ask

logger = get_logger(__name__)


@dataclass
class PTPTrigger:
    """Partial Take Profit trigger configuration."""

    trigger_id: str  # Unique ID for this trigger
    ticket: int
    symbol: str
    trigger_price: float
    close_percentage: float  # Percentage of position to close (e.g., 50.0 for 50%)
    created_at: str
    is_buy: bool
    executed: bool = False
    executed_at: Optional[str] = None
    volume_closed: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PTPTrigger":
        """Create from dictionary."""
        return cls(**data)


class PartialTPManager:
    """Manages Partial Take Profit triggers."""

    def __init__(self):
        """Initialize Partial TP manager."""
        self.conn = get_connection()
        self.pm = get_position_manager()
        self.tm = get_trading_manager()

        # Trigger storage (keyed by trigger_id)
        self.triggers: Dict[str, PTPTrigger] = {}
        self.triggers_file = self._get_triggers_file_path()

        # Monitoring thread
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.check_interval = 0.5  # Check every 500ms

        # Load existing triggers
        self._load_triggers()

        logger.info("Partial TP Manager initialized")

    def _get_triggers_file_path(self) -> str:
        """Get path to triggers storage file."""
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_dir = os.path.join(root_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "partial_tp_triggers.json")

    def _generate_trigger_id(self, ticket: int) -> str:
        """Generate unique trigger ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"{ticket}_{timestamp}"

    def add_trigger(
        self, ticket: int, trigger_price: float, close_percentage: float = 50.0
    ) -> Tuple[bool, str]:
        """
        Add Partial TP trigger for a position.

        Args:
            ticket: Position ticket
            trigger_price: Price at which to trigger partial close
            close_percentage: Percentage of position to close (default: 50%)

        Returns:
            Tuple of (success, message)
        """
        # Validate percentage
        if close_percentage <= 0 or close_percentage >= 100:
            msg = "Close percentage must be between 0 and 100"
            logger.error(msg)
            return False, msg

        # Get position
        position = self.pm.get_position_by_ticket(ticket)
        if position is None:
            msg = f"Position #{ticket} not found"
            logger.error(msg)
            return False, msg

        # Validate trigger price
        if position.is_buy():
            if trigger_price <= position.price_current:
                msg = f"Trigger price must be above current price ({position.price_current})"
                logger.error(msg)
                return False, msg
        else:
            if trigger_price >= position.price_current:
                msg = f"Trigger price must be below current price ({position.price_current})"
                logger.error(msg)
                return False, msg

        # Create trigger
        trigger_id = self._generate_trigger_id(ticket)
        trigger = PTPTrigger(
            trigger_id=trigger_id,
            ticket=ticket,
            symbol=position.symbol,
            trigger_price=trigger_price,
            close_percentage=close_percentage,
            created_at=datetime.now().isoformat(),
            is_buy=position.is_buy(),
        )

        self.triggers[trigger_id] = trigger
        self._save_triggers()

        logger.info(
            f"✓ PTP trigger added for #{ticket} at {trigger_price} ({close_percentage}%)"
        )

        # Start monitoring if not already running
        if not self.monitoring:
            self.start_monitoring()

        return True, f"PTP trigger set at {trigger_price} ({close_percentage}%)"

    def remove_trigger(self, trigger_id: str) -> Tuple[bool, str]:
        """
        Remove Partial TP trigger.

        Args:
            trigger_id: Trigger ID

        Returns:
            Tuple of (success, message)
        """
        if trigger_id not in self.triggers:
            msg = f"Trigger {trigger_id} not found"
            logger.warning(msg)
            return False, msg

        trigger = self.triggers[trigger_id]
        del self.triggers[trigger_id]
        self._save_triggers()

        logger.info(f"✓ PTP trigger {trigger_id} removed for #{trigger.ticket}")
        return True, f"PTP trigger removed"

    def remove_all_for_position(self, ticket: int) -> int:
        """
        Remove all PTP triggers for a position.

        Args:
            ticket: Position ticket

        Returns:
            Number of triggers removed
        """
        to_remove = [
            tid for tid, trigger in self.triggers.items() if trigger.ticket == ticket
        ]

        for trigger_id in to_remove:
            del self.triggers[trigger_id]

        if to_remove:
            self._save_triggers()
            logger.info(f"✓ Removed {len(to_remove)} PTP triggers for #{ticket}")

        return len(to_remove)

    def get_triggers_for_position(self, ticket: int) -> List[PTPTrigger]:
        """Get all triggers for a position."""
        return [
            trigger
            for trigger in self.triggers.values()
            if trigger.ticket == ticket and not trigger.executed
        ]

    def get_all_triggers(self) -> List[PTPTrigger]:
        """Get all active triggers."""
        return [t for t in self.triggers.values() if not t.executed]

    def get_trigger_count(self) -> int:
        """Get count of active triggers."""
        return len([t for t in self.triggers.values() if not t.executed])

    def clear_executed_triggers(self):
        """Remove all executed triggers."""
        self.triggers = {
            trigger_id: trigger
            for trigger_id, trigger in self.triggers.items()
            if not trigger.executed
        }
        self._save_triggers()
        logger.info("Cleared executed PTP triggers")

    def start_monitoring(self):
        """Start background monitoring thread."""
        if self.monitoring:
            logger.warning("PTP monitoring already running")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_triggers, daemon=True, name="PartialTP-Monitor"
        )
        self.monitor_thread.start()
        logger.info("✓ Partial TP monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring thread."""
        if not self.monitoring:
            return

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("✓ Partial TP monitoring stopped")

    def _monitor_triggers(self):
        """Background thread that monitors triggers."""
        logger.info("PTP monitoring thread started")

        while self.monitoring:
            try:
                # Check if connected
                if not self.conn.is_connected():
                    logger.warning("Not connected to MT5, pausing PTP monitoring")
                    time.sleep(5)
                    continue

                # Check each active trigger
                active_triggers = [t for t in self.triggers.values() if not t.executed]

                for trigger in active_triggers:
                    self._check_trigger(trigger)

                # Sleep before next check
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in PTP monitoring thread: {e}", exc_info=True)
                time.sleep(1)

        logger.info("PTP monitoring thread stopped")

    def _check_trigger(self, trigger: PTPTrigger):
        """
        Check if a trigger should be executed.

        Args:
            trigger: PTP trigger to check
        """
        try:
            # Get current position
            position = self.pm.get_position_by_ticket(trigger.ticket)

            if position is None:
                # Position closed, remove trigger
                logger.info(f"Position #{trigger.ticket} closed, removing PTP trigger")
                self.remove_trigger(trigger.trigger_id)
                return

            # Get current price
            if trigger.is_buy:
                current_price = get_current_bid(trigger.symbol)
            else:
                current_price = get_current_ask(trigger.symbol)

            if current_price is None:
                return

            # Check if trigger hit
            triggered = False
            if trigger.is_buy:
                triggered = current_price >= trigger.trigger_price
            else:
                triggered = current_price <= trigger.trigger_price

            if triggered:
                logger.info(f"◎ PTP TRIGGER HIT for #{trigger.ticket}!")
                self._execute_trigger(trigger, position)

        except Exception as e:
            logger.error(
                f"Error checking PTP trigger {trigger.trigger_id}: {e}", exc_info=True
            )

    def _execute_trigger(self, trigger: PTPTrigger, position):
        """
        Execute PTP trigger - close partial position.

        Args:
            trigger: PTP trigger
            position: Position info
        """
        try:
            # Close partial position
            result = self.tm.close_position_custom(
                trigger.ticket, percentage=trigger.close_percentage
            )

            if result.success:
                logger.info(
                    f"✓ PTP executed for #{trigger.ticket} - "
                    f"Closed {trigger.close_percentage}% ({result.volume} lots)"
                )

                # Mark trigger as executed
                trigger.executed = True
                trigger.executed_at = datetime.now().isoformat()
                trigger.volume_closed = result.volume
                self._save_triggers()
            else:
                logger.error(
                    f"✗ Failed to execute PTP for #{trigger.ticket}: "
                    f"{result.error_description}"
                )

        except Exception as e:
            logger.error(
                f"Error executing PTP trigger {trigger.trigger_id}: {e}", exc_info=True
            )

    def _save_triggers(self):
        """Save triggers to file."""
        try:
            data = {
                trigger_id: trigger.to_dict()
                for trigger_id, trigger in self.triggers.items()
            }

            with open(self.triggers_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.triggers)} PTP triggers")

        except Exception as e:
            logger.error(f"Error saving PTP triggers: {e}", exc_info=True)

    def _load_triggers(self):
        """Load triggers from file."""
        try:
            if not os.path.exists(self.triggers_file):
                logger.debug("No existing PTP triggers file")
                return

            with open(self.triggers_file, "r") as f:
                data = json.load(f)

            self.triggers = {
                trigger_id: PTPTrigger.from_dict(trigger_data)
                for trigger_id, trigger_data in data.items()
            }

            active_count = len([t for t in self.triggers.values() if not t.executed])
            logger.info(
                f"Loaded {len(self.triggers)} PTP triggers ({active_count} active)"
            )

            # Start monitoring if there are active triggers
            if active_count > 0:
                self.start_monitoring()

        except Exception as e:
            logger.error(f"Error loading PTP triggers: {e}", exc_info=True)

    def print_triggers(self):
        """Print all triggers to console."""
        active_triggers = [t for t in self.triggers.values() if not t.executed]

        print("\n" + "=" * 100)
        print(f"Partial Take Profit Triggers ({len(active_triggers)} active)")
        print("=" * 100)

        if not active_triggers:
            print("No active triggers")
        else:
            # Group by position
            by_position: Dict[int, List[PTPTrigger]] = {}
            for trigger in active_triggers:
                if trigger.ticket not in by_position:
                    by_position[trigger.ticket] = []
                by_position[trigger.ticket].append(trigger)

            for ticket, triggers in by_position.items():
                print(f"\nPosition #{ticket}:")
                for trigger in sorted(triggers, key=lambda t: t.trigger_price):
                    status = "✓ Executed" if trigger.executed else "⏳ Active"
                    direction = "↑" if trigger.is_buy else "↓"
                    print(
                        f"  {status} {direction} {trigger.symbol} @ {trigger.trigger_price} "
                        f"({trigger.close_percentage}%)"
                    )

        print("=" * 100)

    def __del__(self):
        """Cleanup when manager is destroyed."""
        self.stop_monitoring()


# Global Partial TP manager instance
partial_tp_manager = PartialTPManager()


def get_partial_tp_manager() -> PartialTPManager:
    """
    Get the global Partial TP manager instance.

    Returns:
        PartialTPManager: Global Partial TP manager object
    """
    return partial_tp_manager
