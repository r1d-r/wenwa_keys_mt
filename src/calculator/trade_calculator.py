"""
Contains the TradeCalculator class for performing pre-trade calculations
like lot size, risk/reward, and position value.
"""
import MetaTrader5 as mt5
from src.config.logger import get_logger
from src.mt5_manager.connection import get_connection
from src.mt5_manager.utils import (
    normalize_lot,
    calculate_pips,
    get_current_ask,
    get_current_bid,
)

logger = get_logger(__name__)


class TradeCalculator:
    """Performs all pre-trade calculations."""

    def __init__(self):
        self.conn = get_connection()
        logger.info("TradeCalculator initialized.")

    def calculate_lot_size(
        self, account_balance: float, risk_percent: float, sl_pips: float, symbol: str
    ) -> float:
        """
        Calculates the appropriate lot size for a trade based on risk percentage.
        """
        if not self.conn.is_connected() or sl_pips <= 0 or risk_percent <= 0:
            return 0.0

        symbol_info = self.conn.get_symbol_info(symbol)
        if not symbol_info:
            return 0.0

        # 1. Calculate the monetary risk amount
        risk_amount = account_balance * (risk_percent / 100.0)

        # 2. Get symbol properties
        point = symbol_info.point
        tick_size = symbol_info.trade_tick_size
        calc_mode = symbol_info.trade_calc_mode

        # 3. HYBRID LOGIC: Select the correct tick value based on calculation mode
        log_msg = ""
        if calc_mode == mt5.SYMBOL_CALC_MODE_FOREX:
            # For Forex pairs, broker's value is reliable as it includes currency conversion (e.g., JPY to USD).
            tick_value = symbol_info.trade_tick_value
            log_msg = "Using Broker Tick Value (Forex)"
        else:
            # For CFDs/Metals quoted in account currency, manual calculation is more reliable.
            contract_size = symbol_info.trade_contract_size
            tick_value = contract_size * tick_size
            log_msg = "Using Manual Tick Value (CFD/Metal)"

        # 4. Determine pip size and SL value
        pip_size = point * 10
        pips_to_ticks_ratio = pip_size / tick_size
        sl_value_per_lot = sl_pips * pips_to_ticks_ratio * tick_value

        if sl_value_per_lot <= 0:
            return 0.0

        # 5. Calculate final lot size
        lot_size = risk_amount / sl_value_per_lot
        final_lot_size = normalize_lot(symbol, lot_size)

        value_per_pip_per_lot = pips_to_ticks_ratio * tick_value
        logger.info(
            f"Calc: Balance={account_balance:,.2f}, Risk={risk_percent}%, SL={sl_pips} pips, Symbol={symbol} [{log_msg}]"
        )
        logger.info(
            f" -> Risk Amount={risk_amount:,.2f}, Value per Pip/Lot={value_per_pip_per_lot:,.2f}"
        )
        logger.info(
            f" -> SL Value/Lot={sl_value_per_lot:,.2f}, Raw Lot={lot_size:.4f} -> Normalized Lot={final_lot_size}"
        )

        return final_lot_size

    def calculate_rr(self, symbol, entry_price, sl_price, tp_price):
        if sl_price == 0.0 or tp_price == 0.0:
            return 0.0
        risk_pips = calculate_pips(symbol, entry_price, sl_price)
        reward_pips = calculate_pips(symbol, entry_price, tp_price)
        if risk_pips <= 0:
            return 0.0
        rr_ratio = reward_pips / risk_pips
        logger.info(
            f"R:R Calc: Risk={risk_pips:.1f} pips, Reward={reward_pips:.1f} pips -> Ratio=1:{rr_ratio:.2f}"
        )
        return rr_ratio

    def calculate_pip_distance(
        self, symbol: str, price_start: float, price_end: float
    ) -> float:
        """
        Calculates the distance in pips between two price points.
        This is a wrapper for the utility function to keep calculations within the class.

        Args:
            symbol (str): The symbol to calculate for.
            price_start (float): The starting price.
            price_end (float): The ending price.

        Returns:
            float: The distance in pips (always a positive value).
        """
        pip_distance = calculate_pips(symbol, price_start, price_end)
        logger.info(
            f"Pip Distance Calc: {symbol} from {price_start} to {price_end} = {pip_distance:.1f} pips"
        )
        return pip_distance

    def validate_price_levels(
        self, symbol, order_type, entry_price, sl_price, tp_price
    ):
        ask, bid = get_current_ask(symbol), get_current_bid(symbol)
        if not ask or not bid:
            return False, "Could not fetch market price."
        is_buy = order_type in [
            mt5.ORDER_TYPE_BUY,
            mt5.ORDER_TYPE_BUY_LIMIT,
            mt5.ORDER_TYPE_BUY_STOP,
        ]
        if sl_price != 0.0:
            if is_buy and sl_price >= entry_price:
                return False, "SL for BUY must be below entry."
            if not is_buy and sl_price <= entry_price:
                return False, "SL for SELL must be above entry."
        if tp_price != 0.0:
            if is_buy and tp_price <= entry_price:
                return False, "TP for BUY must be above entry."
            if not is_buy and tp_price >= entry_price:
                return False, "TP for SELL must be below entry."
        if order_type == mt5.ORDER_TYPE_BUY_LIMIT and entry_price >= ask:
            return False, "BUY LIMIT must be below ask."
        if order_type == mt5.ORDER_TYPE_BUY_STOP and entry_price <= ask:
            return False, "BUY STOP must be above ask."
        if order_type == mt5.ORDER_TYPE_SELL_LIMIT and entry_price <= bid:
            return False, "SELL LIMIT must be below bid."
        if order_type == mt5.ORDER_TYPE_SELL_STOP and entry_price >= bid:
            return False, "SELL STOP must be above bid."
        return True, "Price levels are valid."


# --- Singleton Factory ---
_trade_calculator = None


def get_trade_calculator():
    global _trade_calculator
    if _trade_calculator is None:
        _trade_calculator = TradeCalculator()
    return _trade_calculator
