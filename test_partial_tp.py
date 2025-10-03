"""
Test Partial Take Profit trigger system.
"""

from src.mt5_manager.connection import get_connection
from src.mt5_manager.trading import get_trading_manager
from src.mt5_manager.positions import get_position_manager
from src.triggers.partial_tp import get_partial_tp_manager
from src.mt5_manager.utils import pips_to_price
import time

print("\nTesting Partial Take Profit System - DEMO ACCOUNT\n")
print("=" * 100)

# Connect
conn = get_connection()
if not conn.connect():
    print("❌ Failed to connect to MT5")
    exit(1)

tm = get_trading_manager()
pm = get_position_manager()
ptp = get_partial_tp_manager()
symbol = "EURUSD"

print("\n1. Opening test position (0.20 lots for better partial testing)...")
result = tm.buy(symbol, 0.20, comment="Partial TP Test")

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

# Set multiple PTP triggers
print(f"\n2. Setting multiple PTP triggers...")

# PTP 1: 50% at 15 pips
trigger1_price = pips_to_price(symbol, position.price_open, 15, "up")
success, msg = ptp.add_trigger(ticket, trigger1_price, close_percentage=50.0)
print(f"   PTP 1 (50% @ 15 pips): {msg}")

# PTP 2: 30% at 30 pips
trigger2_price = pips_to_price(symbol, position.price_open, 30, "up")
success, msg = ptp.add_trigger(ticket, trigger2_price, close_percentage=30.0)
print(f"   PTP 2 (30% @ 30 pips): {msg}")

print("\n3. Trigger status:")
ptp.print_triggers()

print("\n4. Monitoring for trigger hits...")
print("   Waiting for price to reach trigger levels...")
print("   (This may take a while depending on market movement)")

# Monitor for 2 minutes
for i in range(120):
    triggers = ptp.get_triggers_for_position(ticket)
    active_count = len([t for t in triggers if not t.executed])

    if active_count == 0:
        print(f"\n  ◎ ALL PTP TRIGGERS EXECUTED!")
        break

    # Show status every 10 seconds
    if i % 10 == 0:
        current_bid = conn.get_symbol_info_tick(symbol).bid
        distance_pips = (current_bid - position.price_open) / 0.0001
        print(
            f"   [{i}s] Current: {current_bid:.5f} | "
            f"Distance: {distance_pips:.1f} pips | "
            f"Active triggers: {active_count}"
        )

    time.sleep(1)
else:
    print("\n   ⚠ Timeout waiting for triggers")

print("\n5. Final position status:")
pm.print_position_summary(symbol)

print("\n6. Final trigger status:")
ptp.print_triggers()

input("\nPress ENTER to cleanup and exit...")

# Cleanup
print("\n7. Cleaning up...")
ptp.stop_monitoring()
remaining = pm.get_position_by_ticket(ticket)
if remaining:
    tm.close_position_full(ticket)
ptp.remove_all_for_position(ticket)

print("\n" + "=" * 100)
print("✅ Partial TP system test completed!")
