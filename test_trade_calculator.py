"""
Tests the TradeCalculator class and its methods.
"""

import MetaTrader5 as mt5

from src.mt5_manager.connection import get_connection
from src.calculator.trade_calculator import get_trade_calculator
# CORRECTED: Added imports for price and util functions
from src.mt5_manager.utils import get_current_ask, get_current_bid

print("\nTesting Trade Calculator\n")
print("=" * 100)

# Connect
conn = get_connection()
if not conn.connect():
    print("❌ Failed to connect to MT5. Cannot perform accurate test.")
    exit(1)

# --- Test Data ---
trade_calculator = get_trade_calculator()
test_balance = 50000.0
test_risk_percent = 0.5
test_sl_pips = 25.0
test_symbol = "GBPUSD"  # Using a consistent symbol for all tests

expected_risk_amount = test_balance * (test_risk_percent / 100)
print(
    f"Test Scenario: Account Balance=, Risk={test_risk_percent}%, SL={test_sl_pips} pips"
)
print(f"Expected amount to risk: ")
print("-" * 50)

def run_symbol_test(symbol: str):
    """Runs the lot size calculation for a given symbol and prints results."""
    print(f"Testing Lot Size for symbol: {symbol}...")

    calculated_lot = trade_calculator.calculate_lot_size(
        account_balance=test_balance,
        risk_percent=test_risk_percent,
        sl_pips=test_sl_pips,
        symbol=symbol,
    )

    if calculated_lot > 0:
        print(f"✓ Test passed for Lot Size ({symbol}). Calculated: {calculated_lot}")
    else:
        print(f"❌ Test FAILED for Lot Size ({symbol}). Result was {calculated_lot}.")
    print("")

# --- Run Lot Size Tests ---
run_symbol_test("EURUSD")
run_symbol_test("GBPJPY")
run_symbol_test("XAUUSD")

# --- Test R:R Calculation ---
print("-" * 50)
print("Testing Risk:Reward Calculation...")
entry = 1.25000
sl = 1.24800
tp = 1.25600
expected_rr = 3.0
print(f"Scenario: Entry={entry}, SL={sl} (20 pips), TP={tp} (60 pips)")
rr = trade_calculator.calculate_rr(test_symbol, entry, sl, tp)
if abs(rr - expected_rr) < 0.01:
    print(f"✓ Test passed for R:R. Expected ~{expected_rr:.2f}, Got {rr:.2f}")
else:
    print(f"❌ Test FAILED for R:R. Expected {expected_rr:.2f}, Got {rr:.2f}")

# --- Test Price Level Validation ---
print("-" * 50)
print("Testing Price Level Validation...")
current_ask = get_current_ask(test_symbol)
current_bid = get_current_bid(test_symbol)

scenarios = {
    "VALID BUY LIMIT": (
        True,
        test_symbol,
        mt5.ORDER_TYPE_BUY_LIMIT,
        current_ask - 0.00100,
        current_ask - 0.00200,
        current_ask + 0.00100,
    ),
    "INVALID BUY LIMIT (Entry > Ask)": (
        False,
        test_symbol,
        mt5.ORDER_TYPE_BUY_LIMIT,
        current_ask + 0.00100,
        current_ask - 0.00100,
        current_ask + 0.00200,
    ),
    "VALID BUY STOP": (
        True,
        test_symbol,
        mt5.ORDER_TYPE_BUY_STOP,
        current_ask + 0.00100,
        current_ask - 0.00100,
        current_ask + 0.00200,
    ),
    "INVALID SELL (SL < Entry)": (
        False,
        test_symbol,
        mt5.ORDER_TYPE_SELL,
        current_bid,
        current_bid - 0.00100,
        current_bid - 0.00200,
    ),
    "VALID SELL": (
        True,
        test_symbol,
        mt5.ORDER_TYPE_SELL,
        current_bid,
        current_bid + 0.00100,
        current_bid - 0.00100,
    ),
    "INVALID BUY (TP < Entry)": (
        False,
        test_symbol,
        mt5.ORDER_TYPE_BUY,
        current_ask,
        current_ask + 0.00100,
        current_ask - 0.00100,
    ),
}

for name, (expected, sym, o_type, p_entry, p_sl, p_tp) in scenarios.items():
    is_valid, message = trade_calculator.validate_price_levels(
        sym, o_type, p_entry, p_sl, p_tp
    )
    if is_valid == expected:
        print(f"✓ Test passed for: {name}")
    else:
        print(f"❌ Test FAILED for: {name} - Message: {message}")

# --- Test Pip Distance Calculation ---
print("-" * 50)
print("Testing Pip Distance Calculation...")

price1 = 1.25000
price2 = 1.25255  # Should be 25.5 pips
expected_pips = 25.5

pips = trade_calculator.calculate_pip_distance(test_symbol, price1, price2)
if abs(pips - expected_pips) < 0.01:
    print(
        f"✓ Test passed for Pip Distance. Expected ~{expected_pips:.1f}, Got {pips:.1f}"
    )
else:
    print(
        f"❌ Test FAILED for Pip Distance. Expected {expected_pips:.1f}, Got {pips:.1f}"
    )

# --- Test Position Value Calculation ---
print("-" * 50)
print("Testing Position Value Calculation...")

# Assuming account currency is USD.
# Test 1: Forex (EURUSD). 1 lot = 100,000 EUR. Value in USD = 100,000 * EURUSD price.
eurusd_val = trade_calculator.calculate_position_value("EURUSD", 1.0)
eurusd_price = get_current_ask("EURUSD")
if abs(eurusd_val - (100000 * eurusd_price)) < 1:
    print(f"✓ Test passed for Forex Value (EURUSD). Calculated: ${eurusd_val:,.2f}")
else:
    print(f"❌ Test FAILED for Forex Value (EURUSD).")

# Test 2: Metal (XAUUSD). 1 lot = 100oz. Value in USD = 100 * XAUUSD price.
xauusd_val = trade_calculator.calculate_position_value("XAUUSD", 1.0)
xauusd_price = get_current_ask("XAUUSD")
if abs(xauusd_val - (100 * xauusd_price)) < 1:
    print(f"✓ Test passed for Metal Value (XAUUSD). Calculated: ${xauusd_val:,.2f}")
else:
    print(f"❌ Test FAILED for Metal Value (XAUUSD).")

# Disconnect
conn.disconnect()
print("\n" + "=" * 100)
print("✅ Trade calculator tests completed!")
