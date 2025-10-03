"""
Auto Breakeven (BE) trigger system.
Monitors positions and automatically moves stop loss to entry when trigger price is hit.
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
from src.mt5_manager.modifications import get_position_modifier
from src.mt5_manager.utils import get_current_bid, get_current_ask

logger = get_logger(__name__)


@dataclass
class BETrigger:
    """Auto Breakeven trigger configuration."""

    ticket: int
    symbol: str
    trigger_price: float
    created_at: str
    is_buy: bool
    executed: bool = False
    executed_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BETrigger":
        """Create from dictionary."""
        return cls(**data)


class AutoBEManager:
    """Manages Auto Breakeven triggers."""

    def __init__(self):
        """Initialize Auto BE manager."""
        self.conn = get_connection()
        self.pm = get_position_manager()
        self.mod = get_position_modifier()

        # Trigger storage
        self.triggers: Dict[int, BETrigger] = {}
        self.triggers_file = self._get_triggers_file_path()

        # Monitoring thread
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.check_interval = 0.5  # Check every 500ms

        # Load existing triggers
        self._load_triggers()

        logger.info("Auto BE Manager initialized")

    def _get_triggers_file_path(self) -> str:
        """Get path to triggers storage file."""
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_dir = os.path.join(root_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "auto_be_triggers.json")

    def add_trigger(self, ticket: int, trigger_price: float) -> Tuple[bool, str]:
        """
        Add Auto BE trigger for a position.

        Args:
            ticket: Position ticket
            trigger_price: Price at which to trigger BE

        Returns:
            Tuple of (success, message)
        """
        # Get position
        position = self.pm.get_position_by_ticket(ticket)
        if position is None:
            msg = f"Position #{ticket} not found"
            logger.error(msg)
            return False, msg

        # Validate trigger price
        if position.is_buy():
            if trigger_price <= position.price_open:
                msg = f"Trigger price must be above entry ({position.price_open})"
                logger.error(msg)
                return False, msg
        else:
            if trigger_price >= position.price_open:
                msg = f"Trigger price must be below entry ({position.price_open})"
                logger.error(msg)
                return False, msg

        # Create trigger
        trigger = BETrigger(
            ticket=ticket,
            symbol=position.symbol,
            trigger_price=trigger_price,
            created_at=datetime.now().isoformat(),
            is_buy=position.is_buy(),
        )

        self.triggers[ticket] = trigger
        self._save_triggers()

        logger.info(f"✓ BE trigger added for #{ticket} at {trigger_price}")

        # Start monitoring if not already running
        if not self.monitoring:
            self.start_monitoring()

        return True, f"BE trigger set at {trigger_price}"

    def remove_trigger(self, ticket: int) -> Tuple[bool, str]:
        """
        Remove Auto BE trigger.

        Args:
            ticket: Position ticket

        Returns:
            Tuple of (success, message)
        """
        if ticket not in self.triggers:
            msg = f"No BE trigger found for #{ticket}"
            logger.warning(msg)
            return False, msg

        del self.triggers[ticket]
        self._save_triggers()

        logger.info(f"✓ BE trigger removed for #{ticket}")
        return True, f"BE trigger removed for #{ticket}"

    def get_trigger(self, ticket: int) -> Optional[BETrigger]:
        """Get trigger for a position."""
        return self.triggers.get(ticket)

    def get_all_triggers(self) -> List[BETrigger]:
        """Get all active triggers."""
        return [t for t in self.triggers.values() if not t.executed]

    def get_trigger_count(self) -> int:
        """Get count of active triggers."""
        return len([t for t in self.triggers.values() if not t.executed])

    def clear_executed_triggers(self):
        """Remove all executed triggers."""
        self.triggers = {
            ticket: trigger
            for ticket, trigger in self.triggers.items()
            if not trigger.executed
        }
        self._save_triggers()
        logger.info("Cleared executed BE triggers")

    def start_monitoring(self):
        """Start background monitoring thread."""
        if self.monitoring:
            logger.warning("BE monitoring already running")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_triggers, daemon=True, name="AutoBE-Monitor"
        )
        self.monitor_thread.start()
        logger.info("✓ Auto BE monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring thread."""
        if not self.monitoring:
            return

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("✓ Auto BE monitoring stopped")

    def _monitor_triggers(self):
        """Background thread that monitors triggers."""
        logger.info("BE monitoring thread started")

        while self.monitoring:
            try:
                # Check if connected
                if not self.conn.is_connected():
                    logger.warning("Not connected to MT5, pausing BE monitoring")
                    time.sleep(5)
                    continue

                # Check each active trigger
                active_triggers = [t for t in self.triggers.values() if not t.executed]

                for trigger in active_triggers:
                    self._check_trigger(trigger)

                # Sleep before next check
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in BE monitoring thread: {e}", exc_info=True)
                time.sleep(1)

        logger.info("BE monitoring thread stopped")

    def _check_trigger(self, trigger: BETrigger):
        """
        Check if a trigger should be executed.

        Args:
            trigger: BE trigger to check
        """
        try:
            # Get current position
            position = self.pm.get_position_by_ticket(trigger.ticket)

            if position is None:
                # Position closed, remove trigger
                logger.info(f"Position #{trigger.ticket} closed, removing BE trigger")
                self.remove_trigger(trigger.ticket)
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
                logger.info(f"✓ BE TRIGGER HIT for #{trigger.ticket}!")
                self._execute_trigger(trigger, position)

        except Exception as e:
            logger.error(
                f"Error checking BE trigger #{trigger.ticket}: {e}", exc_info=True
            )

    def _execute_trigger(self, trigger: BETrigger, position):
        """
        Execute BE trigger - move SL to entry.

        Args:
            trigger: BE trigger
            position: Position info
        """
        try:
            # Move SL to entry
            result = self.mod.set_sl_to_entry(trigger.ticket)

            if result.success:
                logger.info(f"✓ BE executed for #{trigger.ticket} - SL moved to entry")

                # Mark trigger as executed
                trigger.executed = True
                trigger.executed_at = datetime.now().isoformat()
                self._save_triggers()
            else:
                logger.error(
                    f"✗ Failed to execute BE for #{trigger.ticket}: {result.error_description}"
                )

        except Exception as e:
            logger.error(
                f"Error executing BE trigger #{trigger.ticket}: {e}", exc_info=True
            )

    def _save_triggers(self):
        """Save triggers to file."""
        try:
            data = {
                ticket: trigger.to_dict() for ticket, trigger in self.triggers.items()
            }

            with open(self.triggers_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.triggers)} BE triggers")

        except Exception as e:
            logger.error(f"Error saving BE triggers: {e}", exc_info=True)

    def _load_triggers(self):
        """Load triggers from file."""
        try:
            if not os.path.exists(self.triggers_file):
                logger.debug("No existing BE triggers file")
                return

            with open(self.triggers_file, "r") as f:
                data = json.load(f)

            self.triggers = {
                int(ticket): BETrigger.from_dict(trigger_data)
                for ticket, trigger_data in data.items()
            }

            active_count = len([t for t in self.triggers.values() if not t.executed])
            logger.info(
                f"Loaded {len(self.triggers)} BE triggers ({active_count} active)"
            )

            # Start monitoring if there are active triggers
            if active_count > 0:
                self.start_monitoring()

        except Exception as e:
            logger.error(f"Error loading BE triggers: {e}", exc_info=True)

    def print_triggers(self):
        """Print all triggers to console."""
        active_triggers = [t for t in self.triggers.values() if not t.executed]

        print("\n" + "=" * 100)
        print(f"Auto Breakeven Triggers ({len(active_triggers)} active)")
        print("=" * 100)

        if not active_triggers:
            print("No active triggers")
        else:
            for trigger in active_triggers:
                status = "✓ Executed" if trigger.executed else "⏳ Active"
                direction = "↑" if trigger.is_buy else "↓"
                print(
                    f"{status} {direction} #{trigger.ticket} {trigger.symbol} @ {trigger.trigger_price}"
                )

        print("=" * 100)

    def __del__(self):
        """Cleanup when manager is destroyed."""
        self.stop_monitoring()


# Global Auto BE manager instance
auto_be_manager = AutoBEManager()


def get_auto_be_manager() -> AutoBEManager:
    """
    Get the global Auto BE manager instance.

    Returns:
        AutoBEManager: Global Auto BE manager object
    """
    return auto_be_manager
