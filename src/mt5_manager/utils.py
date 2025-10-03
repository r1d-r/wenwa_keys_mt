"""
Utility functions for MetaTrader 5 operations.
Provides helper functions for pip calculations, lot sizing, and data conversions.
"""

import MetaTrader5 as mt5
from typing import Optional, List, Dict, Any
from enum import Enum
from src.config.logger import get_logger
from src.mt5_manager.connection import get_connection

logger = get_logger(__name__)


class OrderType(Enum):
    """Order type enumeration."""
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP


class TradeAction(Enum):
    """Trade action enumeration."""
    DEAL = mt5.TRADE_ACTION_DEAL
    PENDING = mt5.TRADE_ACTION_PENDING
    SLTP = mt5.TRADE_ACTION_SLTP
    MODIFY = mt5.TRADE_ACTION_MODIFY
    REMOVE = mt5.TRADE_ACTION_REMOVE


def normalize_price(symbol: str, price: float) -> float:
    """
    Normalize price to symbol's digit precision.
    
    Args:
        symbol: Symbol name
        price: Price to normalize
        
    Returns:
        Normalized price
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info is None:
        logger.error(f"Cannot normalize price for unknown symbol: {symbol}")
        return price
    
    digits = symbol_info.digits
    normalized = round(price, digits)
    
    return normalized


def normalize_lot(symbol: str, lot: float) -> float:
    """
    Normalize lot size to symbol's volume step.
    
    Args:
        symbol: Symbol name
        lot: Lot size to normalize
        
    Returns:
        Normalized lot size
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info is None:
        logger.error(f"Cannot normalize lot for unknown symbol: {symbol}")
        return lot
    
    # Get volume constraints
    min_volume = symbol_info.volume_min
    max_volume = symbol_info.volume_max
    volume_step = symbol_info.volume_step
    
    # Normalize to step
    normalized = round(lot / volume_step) * volume_step
    
    # Apply constraints
    normalized = max(min_volume, min(normalized, max_volume))
    
    # Round to appropriate decimal places
    if volume_step >= 1.0:
        normalized = round(normalized, 0)
    elif volume_step >= 0.1:
        normalized = round(normalized, 1)
    else:
        normalized = round(normalized, 2)
    
    return normalized


def calculate_pips(symbol: str, price1: float, price2: float) -> float:
    """
    Calculate pip distance between two prices.
    
    Args:
        symbol: Symbol name
        price1: First price
        price2: Second price
        
    Returns:
        Pip distance (always positive)
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info is None:
        logger.error(f"Cannot calculate pips for unknown symbol: {symbol}")
        return 0.0
    
    point = symbol_info.point
    digits = symbol_info.digits
    
    # For JPY pairs (2-3 digits), 1 pip = 0.01
    # For other pairs (4-5 digits), 1 pip = 0.0001
    if digits == 2 or digits == 3:
        pip_value = 0.01
    else:
        pip_value = 0.0001
    
    pips = abs(price1 - price2) / pip_value
    
    return round(pips, 1)


def pips_to_price(symbol: str, base_price: float, pips: float, direction: str = "up") -> float:
    """
    Convert pips to price distance from base price.
    
    Args:
        symbol: Symbol name
        base_price: Base price to calculate from
        pips: Number of pips
        direction: "up" or "down"
        
    Returns:
        Target price
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info is None:
        logger.error(f"Cannot convert pips to price for unknown symbol: {symbol}")
        return base_price
    
    digits = symbol_info.digits
    
    # Determine pip value
    if digits == 2 or digits == 3:
        pip_value = 0.01
    else:
        pip_value = 0.0001
    
    # Calculate price difference
    price_diff = pips * pip_value
    
    # Apply direction
    if direction.lower() == "up":
        target_price = base_price + price_diff
    else:
        target_price = base_price - price_diff
    
    return normalize_price(symbol, target_price)


def get_point_value(symbol: str) -> float:
    """
    Get the point value for a symbol.
    
    Args:
        symbol: Symbol name
        
    Returns:
        Point value
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info is None:
        logger.error(f"Cannot get point value for unknown symbol: {symbol}")
        return 0.00001
    
    return symbol_info.point


def get_pip_value(symbol: str) -> float:
    """
    Get the pip value for a symbol.
    
    Args:
        symbol: Symbol name
        
    Returns:
        Pip value (0.01 for JPY pairs, 0.0001 for others)
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info is None:
        logger.error(f"Cannot get pip value for unknown symbol: {symbol}")
        return 0.0001
    
    digits = symbol_info.digits
    
    if digits == 2 or digits == 3:
        return 0.01
    else:
        return 0.0001


def is_buy_order(order_type: int) -> bool:
    """
    Check if order type is a buy order.
    
    Args:
        order_type: MT5 order type constant
        
    Returns:
        True if buy order
    """
    return order_type in [
        mt5.ORDER_TYPE_BUY,
        mt5.ORDER_TYPE_BUY_LIMIT,
        mt5.ORDER_TYPE_BUY_STOP
    ]


def is_sell_order(order_type: int) -> bool:
    """
    Check if order type is a sell order.
    
    Args:
        order_type: MT5 order type constant
        
    Returns:
        True if sell order
    """
    return order_type in [
        mt5.ORDER_TYPE_SELL,
        mt5.ORDER_TYPE_SELL_LIMIT,
        mt5.ORDER_TYPE_SELL_STOP
    ]


def get_order_type_string(order_type: int) -> str:
    """
    Convert order type constant to readable string.
    
    Args:
        order_type: MT5 order type constant
        
    Returns:
        Order type as string
    """
    order_types = {
        mt5.ORDER_TYPE_BUY: "BUY",
        mt5.ORDER_TYPE_SELL: "SELL",
        mt5.ORDER_TYPE_BUY_LIMIT: "BUY LIMIT",
        mt5.ORDER_TYPE_SELL_LIMIT: "SELL LIMIT",
        mt5.ORDER_TYPE_BUY_STOP: "BUY STOP",
        mt5.ORDER_TYPE_SELL_STOP: "SELL STOP"
    }
    return order_types.get(order_type, f"UNKNOWN ({order_type})")


def validate_symbol(symbol: str) -> bool:
    """
    Check if symbol is valid and available.
    
    Args:
        symbol: Symbol name
        
    Returns:
        True if valid and available
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info is None:
        return False
    
    # Check if trading is allowed
    if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
        logger.warning(f"Trading not fully allowed for symbol: {symbol}")
        return False
    
    return True


def get_current_symbol() -> Optional[str]:
    """
    Get the symbol of the currently active chart.
    
    Returns:
        Symbol name or None
    """
    try:
        # Get the symbol of the current chart
        symbol = mt5.symbol_name()
        if symbol:
            return symbol
        
        # Fallback: get first symbol from market watch
        symbols = mt5.symbols_get()
        if symbols and len(symbols) > 0:
            return symbols[0].name
        
        return None
    except:
        return None


def get_current_bid(symbol: str) -> Optional[float]:
    """
    Get current bid price for symbol.
    
    Args:
        symbol: Symbol name
        
    Returns:
        Bid price or None
    """
    conn = get_connection()
    tick = conn.get_symbol_info_tick(symbol)
    
    if tick:
        return tick.bid
    return None


def get_current_ask(symbol: str) -> Optional[float]:
    """
    Get current ask price for symbol.
    
    Args:
        symbol: Symbol name
        
    Returns:
        Ask price or None
    """
    conn = get_connection()
    tick = conn.get_symbol_info_tick(symbol)
    
    if tick:
        return tick.ask
    return None


def get_spread(symbol: str) -> Optional[int]:
    """
    Get current spread in points.
    
    Args:
        symbol: Symbol name
        
    Returns:
        Spread in points or None
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info:
        return symbol_info.spread
    return None


def calculate_position_profit(symbol: str, order_type: int, 
                               entry_price: float, current_price: float,
                               volume: float) -> float:
    """
    Calculate position profit/loss.
    
    Args:
        symbol: Symbol name
        order_type: Order type (buy/sell)
        entry_price: Entry price
        current_price: Current price
        volume: Position volume
        
    Returns:
        Profit/loss in account currency
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info is None:
        return 0.0
    
    # Calculate price difference
    if is_buy_order(order_type):
        price_diff = current_price - entry_price
    else:
        price_diff = entry_price - current_price
    
    # Calculate profit
    tick_value = symbol_info.trade_tick_value
    tick_size = symbol_info.trade_tick_size
    
    profit = (price_diff / tick_size) * tick_value * volume
    
    return round(profit, 2)


def format_volume(volume: float) -> str:
    """
    Format volume for display.
    
    Args:
        volume: Volume to format
        
    Returns:
        Formatted volume string
    """
    if volume >= 1.0:
        return f"{volume:.2f}"
    else:
        return f"{volume:.2f}".rstrip('0').rstrip('.')


def format_price(symbol: str, price: float) -> str:
    """
    Format price according to symbol digits.
    
    Args:
        symbol: Symbol name
        price: Price to format
        
    Returns:
        Formatted price string
    """
    conn = get_connection()
    symbol_info = conn.get_symbol_info(symbol)
    
    if symbol_info is None:
        return f"{price:.5f}"
    
    digits = symbol_info.digits
    return f"{price:.{digits}f}"


# Example usage and testing
if __name__ == "__main__":
    print("\nTesting MT5 Utility Functions\n")
    print("=" * 80)
    
    conn = get_connection()
    if not conn.connect():
        print("❌ Failed to connect to MT5")
        exit(1)
    
    symbol = "EURUSD"
    
    # Test symbol validation
    print(f"\n1. Symbol Validation:")
    print(f"   {symbol} is valid: {validate_symbol(symbol)}")
    
    # Test current prices
    print(f"\n2. Current Prices:")
    bid = get_current_bid(symbol)
    ask = get_current_ask(symbol)
    spread = get_spread(symbol)
    print(f"   Bid: {bid}")
    print(f"   Ask: {ask}")
    print(f"   Spread: {spread} points")
    
    # Test pip calculations
    print(f"\n3. Pip Calculations:")
    price1 = 1.09500
    price2 = 1.09550
    pips = calculate_pips(symbol, price1, price2)
    print(f"   Distance between {price1} and {price2}: {pips} pips")
    
    # Test pips to price conversion
    print(f"\n4. Pips to Price Conversion:")
    base_price = 1.09500
    target_up = pips_to_price(symbol, base_price, 20, "up")
    target_down = pips_to_price(symbol, base_price, 20, "down")
    print(f"   Base: {base_price}")
    print(f"   +20 pips: {target_up}")
    print(f"   -20 pips: {target_down}")
    
    # Test lot normalization
    print(f"\n5. Lot Normalization:")
    test_lots = [0.01, 0.05, 0.123, 1.0, 2.567]
    for lot in test_lots:
        normalized = normalize_lot(symbol, lot)
        print(f"   {lot} → {normalized}")
    
    # Test price normalization
    print(f"\n6. Price Normalization:")
    test_prices = [1.095001234, 1.09500, 1.095]
    for price in test_prices:
        normalized = normalize_price(symbol, price)
        print(f"   {price} → {normalized}")
    
    # Test order type checks
    print(f"\n7. Order Type Checks:")
    print(f"   BUY is buy order: {is_buy_order(mt5.ORDER_TYPE_BUY)}")
    print(f"   SELL is sell order: {is_sell_order(mt5.ORDER_TYPE_SELL)}")
    print(f"   BUY type string: {get_order_type_string(mt5.ORDER_TYPE_BUY)}")
    
    # Test profit calculation
    print(f"\n8. Profit Calculation:")
    profit = calculate_position_profit(symbol, mt5.ORDER_TYPE_BUY, 1.09500, 1.09550, 0.10)
    print(f"   BUY 0.10 lots @ 1.09500, current 1.09550")
    print(f"   Profit: ${profit:.2f}")
    
    conn.disconnect()
    print("\n" + "=" * 80)
    print("✅ All utility function tests completed!")
