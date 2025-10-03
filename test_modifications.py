"""
Test SL/TP modification functions.
"""

from src.mt5_manager.connection import get_connection
from src.mt5_manager.trading import get_trading_manager
from src.mt5_manager.positions import get_position_manager
from src.mt5_manager.modifications import get_position_modifier
from src.mt5_manager.utils import pips_to_price
import time

print("\nTesting SL/TP Modification Functions - DEMO ACCOUNT\n")
print("=" * 100)

# Connect
conn = get_connection()
if not conn.connect():
    print("❌ Failed to connect to MT5")
    exit(1)

tm = get_trading_manager()
pm = get_position_manager()
mod = get_position_modifier()
symbol = "EURUSD"

# Step 1: Open a test position with SL and TP
print("\n1. Opening test position with SL/TP...")
current_ask = conn.get_symbol_info_tick(symbol).ask
sl_price = pips_to_price(symbol, current_ask, 20, "down")
tp_price = pips_to_price(symbol, current_ask, 40, "up")

result = tm.buy(symbol, 0.10, sl=sl_price, tp=tp_price, 
                comment="Test Modification")

if not result.success:
    print(f"❌ Failed to open position: {result.error_description}")
    conn.disconnect()
    exit(1)

ticket = result.order_ticket
print(f"✓ Position opened: #{ticket}")

time.sleep(2)
pm.print_position_summary(symbol)

input("\nPress ENTER to test modifying SL...")

# Step 2: Modify SL
print("\n2. Testing SL modification (move 10 pips closer)...")
position = pm.get_position_by_ticket(ticket)
new_sl = pips_to_price(symbol, position.price_open, 10, "down")
result = mod.modify_position(ticket, sl=new_sl)
print(f"   {result}")

time.sleep(1)
pm.print_position_summary(symbol)

input("\nPress ENTER to test modifying TP...")

# Step 3: Modify TP
print("\n3. Testing TP modification (set at 1:3 R:R)...")
result = mod.set_tp_by_rr(ticket, risk_reward=3.0)
print(f"   {result}")

time.sleep(1)
pm.print_position_summary(symbol)

input("\nPress ENTER to test SL @entry (wait for profit first)...")

# Step 4: Wait for profit and test SL @entry
print("\n4. Testing SL @entry...")
print("   Waiting for position to be in profit...")

for i in range(30):  # Wait up to 30 seconds
    position = pm.get_position_by_ticket(ticket)
    if position and position.is_profitable():
        print(f"   ✓ Position in profit: {position.profit_pips:.1f} pips")
        break
    time.sleep(1)
    if (i + 1) % 5 == 0:
        print(f"   Still waiting... ({i+1}s)")
else:
    print("   ⚠ Position not in profit yet, testing anyway...")

result = mod.set_sl_to_entry(ticket)
print(f"   {result}")

time.sleep(1)
pm.print_position_summary(symbol)

input("\nPress ENTER to test SL in profit...")

# Step 5: Test SL in profit
print("\n5. Testing SL in profit (5 pips)...")
result = mod.set_sl_to_profit(ticket, pips_in_profit=5.0)
print(f"   {result}")

time.sleep(1)
pm.print_position_summary(symbol)

input("\nPress ENTER to close position and finish test...")

# Step 6: Close position
print("\n6. Closing test position...")
result = tm.close_position_full(ticket)
print(f"   {result}")

time.sleep(1)
pm.print_position_summary(symbol)

# Disconnect
conn.disconnect()
print("\n" + "=" * 100)
print("✅ SL/TP modification tests completed!")
