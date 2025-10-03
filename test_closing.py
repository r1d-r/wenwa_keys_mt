"""
Test position closing functions.
Opens positions and then tests closing them.
"""

from src.mt5_manager.connection import get_connection
from src.mt5_manager.trading import get_trading_manager
from src.mt5_manager.positions import get_position_manager
import time

print("\nTesting Position Closing Functions - DEMO ACCOUNT\n")
print("=" * 100)

# Connect
conn = get_connection()
if not conn.connect():
    print("❌ Failed to connect to MT5")
    exit(1)

tm = get_trading_manager()
pm = get_position_manager()
symbol = "EURUSD"

# Step 1: Open some test positions
print("\n1. Opening test positions...")
print("   Opening 3 BUY positions of 0.01 lots each")

tickets = []
for i in range(3):
    result = tm.buy(symbol, 0.01, comment=f"Test Position {i+1}")
    if result.success:
        print(f"   ✓ Position {i+1} opened: #{result.order_ticket}")
        tickets.append(result.order_ticket)
        time.sleep(0.5)  # Small delay between orders
    else:
        print(f"   ✗ Failed to open position {i+1}: {result.error_description}")

if not tickets:
    print("\n❌ No positions opened. Cannot test closing.")
    conn.disconnect()
    exit(1)

print(f"\n   Successfully opened {len(tickets)} positions")

# Wait a moment
time.sleep(2)

# Step 2: Show current positions
print("\n2. Current positions:")
pm.print_position_summary(symbol)

input("\n   Press ENTER to test CLOSE FULL on first position...")

# Step 3: Test close full
print("\n3. Testing CLOSE FULL:")
if len(tickets) > 0:
    result = tm.close_position_full(tickets[0])
    print(f"   {result}")
    time.sleep(1)
    pm.print_position_summary(symbol)

input("\n   Press ENTER to test CLOSE HALF on second position...")

# Step 4: Test close half
print("\n4. Testing CLOSE HALF:")
if len(tickets) > 1:
    result = tm.close_position_half(tickets[1])
    print(f"   {result}")
    time.sleep(1)
    pm.print_position_summary(symbol)

input("\n   Press ENTER to test CLOSE CUSTOM (25%) on third position...")

# Step 5: Test close custom
print("\n5. Testing CLOSE CUSTOM (25%):")
if len(tickets) > 2:
    result = tm.close_position_custom(tickets[2], percentage=25.0)
    print(f"   {result}")
    time.sleep(1)
    pm.print_position_summary(symbol)

input("\n   Press ENTER to CLOSE ALL remaining positions...")

# Step 6: Close all remaining
print("\n6. Closing all remaining positions:")
results = tm.close_all_positions(symbol)
for ticket, result in results.items():
    print(f"   {result}")

time.sleep(1)
pm.print_position_summary(symbol)

# Disconnect
conn.disconnect()
print("\n" + "=" * 100)
print("✅ Position closing tests completed!")
