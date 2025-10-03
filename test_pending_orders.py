import time
import MetaTrader5 as mt5

from src.mt5_manager.connection import get_connection
from src.mt5_manager.trading import get_trading_manager
from src.mt5_manager.utils import pips_to_price

print("\nTesting Pending Order Functions - DEMO ACCOUNT\n")
print("=" * 100)

# Connect
conn = get_connection()
if not conn.connect():
    print("❌ Failed to connect to MT5")
    exit(1)

tm = get_trading_manager()
symbol = "EURUSD"
order_ticket = None  # To store the ticket of our pending order

try:
    # 1. Calculate prices for a BUY LIMIT
    print("\n1. Calculating prices for a test BUY LIMIT order...")
    current_bid = conn.get_symbol_info_tick(symbol).bid

    if not current_bid:
        raise Exception(f"Could not get current price for {symbol}")

    entry_price = pips_to_price(symbol, current_bid, 50, "down")
    sl_price = pips_to_price(symbol, entry_price, 20, "down")
    tp_price = pips_to_price(symbol, entry_price, 100, "up")

    print(f"   Current Bid: {current_bid}")
    print(f"   Calculated Entry (50 pips below): {entry_price}")
    print(f"   Calculated SL: {sl_price}")
    print(f"   Calculated TP: {tp_price}")

    input("\nPress ENTER to place the pending order...")

    # 2. Place the BUY LIMIT order
    print("\n2. Placing the BUY LIMIT order...")
    result = tm.place_pending_order(
        symbol=symbol,
        order_type=mt5.ORDER_TYPE_BUY_LIMIT,
        volume=0.01,
        entry_price=entry_price,
        sl=sl_price,
        tp=tp_price,
        comment="Test BUY LIMIT",
    )

    if not result.success:
        raise Exception(f"Failed to place pending order: {result.error_description}")

    order_ticket = result.order_ticket
    print(f"✓ Pending order placed: #{order_ticket}")

    # 3. Verify the order exists
    print("\n3. Verifying the order exists...")
    time.sleep(1)
    pending_orders = mt5.orders_get(symbol=symbol)
    found = any(order.ticket == order_ticket for order in pending_orders)

    if found:
        print(f"✓ VERIFIED: Pending order #{order_ticket} is active.")
    else:
        print(f"❌ VERIFICATION FAILED: Could not find pending order #{order_ticket}.")

    input("\nPress ENTER to cancel the pending order and finish the test...")

except Exception as e:
    print(f"❌ An error occurred during the test: {e}")

finally:
    # 4. Cleanup: Cancel the pending order
    if order_ticket:
        print(f"\n4. Cleaning up by cancelling pending order #{order_ticket}...")

        delete_request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": order_ticket,
        }
        delete_result = mt5.order_send(delete_request)

        if delete_result and delete_result.retcode == mt5.TRADE_RETCODE_DONE:
            print("✓ Pending order successfully cancelled.")
        else:
            print(f"❌ CLEANUP FAILED: Could not cancel pending order.")
            last_error = mt5.last_error()
            print(f"   Error: {last_error}")

    # Disconnect
    conn.disconnect()
    print("\n" + "=" * 100)
    print("✅ Pending order tests completed!")
