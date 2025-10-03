"""
Tests the TradeCalculator class and its lot size calculation method.
"""

from src.mt5_manager.connection import get_connection
from src.calculator.trade_calculator import get_trade_calculator

print("\nTesting Trade Calculator\n")
print("=" * 100)

# Connect to get live symbol data for accurate testing
conn = get_connection()
if not conn.connect():
    print("❌ Failed to connect to MT5. Cannot perform accurate test.")
    exit(1)

# --- Test Data ---
trade_calculator = get_trade_calculator()
test_balance = 50000.0
test_risk_percent = 0.5  # Risking 0.5%
test_sl_pips = 25.0

expected_risk_amount = test_balance * (test_risk_percent / 100)
print(
    f"Test Scenario: Account Balance=, Risk={test_risk_percent}%, SL={test_sl_pips} pips"
)
print(f"Expected amount to risk: ")
print("-" * 50)


def run_symbol_test(symbol: str):
    """Runs the lot size calculation for a given symbol and prints results."""
    print(f"Testing for symbol: {symbol}...")

    calculated_lot = trade_calculator.calculate_lot_size(
        account_balance=test_balance,
        risk_percent=test_risk_percent,
        sl_pips=test_sl_pips,
        symbol=symbol,
    )

    if calculated_lot > 0:
        print(f"✓ Test passed for {symbol}. Calculated lot size: {calculated_lot}")
    else:
        print(f"❌ Test FAILED for {symbol}. Result was {calculated_lot}.")
    print("")


# --- Run Tests ---
run_symbol_test("EURUSD")
run_symbol_test("GBPJPY")
run_symbol_test(
    "US500Cash"
)  # S&P 500, adjust symbol name if needed (e.g., SPX500, US500)
run_symbol_test("XAUUSD")  # Gold

# --- Test R:R Calculation ---
print("-" * 50)
print("Testing Risk:Reward Calculation...")

# Test Scenario: 20 pips risk, 60 pips reward, should be 1:3
entry = 1.25000
sl = 1.24800
tp = 1.25600
expected_rr = 3.0
test_symbol = "GBPUSD"  # Using a non-JPY pair for standard calculation

print(f"Scenario: Entry={entry}, SL={sl} (20 pips), TP={tp} (60 pips)")

rr = trade_calculator.calculate_rr(
    symbol=test_symbol, entry_price=entry, sl_price=sl, tp_price=tp
)

if abs(rr - expected_rr) < 0.01:
    print(
        f"✓ Test passed for R:R calculation. Expected ~{expected_rr:.2f}, Got {rr:.2f}"
    )
else:
    print(
        f"❌ Test FAILED for R:R calculation. Expected {expected_rr:.2f}, Got {rr:.2f}"
    )

# Disconnect
conn.disconnect()
print("\n" + "=" * 100)
print("✅ Trade calculator tests completed!")
