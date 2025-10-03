"""
Test Auto Breakeven trigger system.
"""

from src.mt5_manager.connection import get_connection
from src.mt5_manager.trading import get_trading_manager
from src.mt5_manager.positions import get_position_manager
from src.triggers.auto_be import get_auto_be_manager
from src.mt5_manager.utils import pips_to_price
import time

print("\nTesting Auto Breakeven System - DEMO ACCOUNT\n")
print("=" * 100)

# Connect
conn = get_connection()
if not conn.connect():
    print("❌ Failed to connect to MT5")
    exit(1)

tm = get_trading_manager()
pm = get_position_manager()
be = get_auto_be_manager()
symbol = "EURUSD"

print("\n1. Opening test position...")
result = tm.buy(symbol, 0.10, comment="Auto BE Test")

if not result.success:
    print(f"❌ Failed to open position: {result.error_description}")
    conn.disconnect()
    exit(1)

ticket = result.order_ticket
print(f"✓ Position opened: #{ticket}")

time.sleep(2)
pm.print_position_summary(symbol)

# Get position details
position = pm.get_position_by_ticket(ticket)
if not position:
    print("❌ Cannot retrieve position")
    conn.disconnect()
    exit(1)

# Set BE trigger 10 pips above entry
trigger_price = pips_to_price(symbol, position.price_open, 10, "up")

print(f"\n2. Setting Auto BE trigger at {trigger_price} (10 pips above entry)...")
success, msg = be.add_trigger(ticket, trigger_price)
print(f"   {msg}")

if not success:
    print("❌ Failed to set BE trigger")
    tm.close_position_full(ticket)
    conn.disconnect()
    exit(1)

print("\n3. Trigger status:")
be.print_triggers()

print("\n4. Monitoring for trigger hit...")
print("   Waiting for price to reach trigger level...")
print("   (This may take a while depending on market movement)")
print("   You can also manually adjust the price in MT5 for faster testing")

# Monitor for trigger execution
for i in range(120):  # Wait up to 2 minutes
    trigger = be.get_trigger(ticket)
    if trigger and trigger.executed:
        print(f"\n ✓ BE TRIGGER EXECUTED!")
        break

    # Show current price vs trigger every 10 seconds
    if i % 10 == 0:
        current_bid = conn.get_symbol_info_tick(symbol).bid
        distance_pips = (current_bid - position.price_open) / 0.0001
        print(
            f"   [{i}s] Current: {current_bid:.5f} | "
            f"Trigger: {trigger_price:.5f} | "
            f"Distance: {distance_pips:.1f} pips from entry"
        )

    time.sleep(1)
else:
    print("\n   ⚠ Timeout waiting for trigger")

print("\n5. Final position status:")
pm.print_position_summary(symbol)

print("\n6. Final trigger status:")
be.print_triggers()

input("\nPress ENTER to close position and stop monitoring...")

# Cleanup
print("\n7. Cleaning up...")
be.stop_monitoring()
tm.close_position_full(ticket)
be.remove_trigger(ticket)

print("\n" + "=" * 100)
print("✅ Auto BE system test completed!")
