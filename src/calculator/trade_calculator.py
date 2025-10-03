"""
Contains the TradeCalculator class for performing pre-trade calculations
like lot size, risk/reward, and position value.
"""

from src.config.logger import get_logger
from src.mt5_manager.connection import get_connection
from src.mt5_manager.utils import normalize_lot, calculate_pips

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

        Args:
            account_balance (float): The total account balance.
            risk_percent (float): The percentage of the account to risk (e.g., 1.0 for 1%).
            sl_pips (float): The stop loss distance in pips.
            symbol (str): The symbol for the trade (e.g., "EURUSD").

        Returns:
            float: The calculated lot size, normalized for the symbol. Returns 0.0 on failure.
        """
        if not self.conn.is_connected():
            logger.error("Cannot calculate lot size, MT5 connection not available.")
            return 0.0

        if sl_pips <= 0 or risk_percent <= 0:
            logger.warning("SL pips and risk percent must be positive values.")
            return 0.0

        symbol_info = self.conn.get_symbol_info(symbol)
        if not symbol_info:
            logger.error(f"Could not retrieve symbol info for {symbol}.")
            return 0.0

        # 1. Calculate the monetary risk amount
        risk_amount = account_balance * (risk_percent / 100.0)

        # 2. Get correct symbol properties from the SymbolInfo object
        point = symbol_info.point
        # CORRECTED ATTRIBUTE NAMES:
        tick_value = symbol_info.trade_tick_value
        tick_size = symbol_info.trade_tick_size

        # Determine the pip size (0.0001 for 4-digit forex, 0.01 for JPY pairs)
        pip_size = 0.0001 if symbol_info.digits in [4, 5] else 0.01

        # 3. Calculate the monetary value of the stop loss for one lot
        if tick_size <= 0:
            logger.error(f"Invalid tick_size ({tick_size}) for symbol {symbol}.")
            return 0.0

        # Value of a 1 pip move for 1 lot
        value_per_pip = (pip_size / tick_size) * tick_value

        # Total value of the stop loss
        sl_value_per_lot = sl_pips * value_per_pip

        if sl_value_per_lot <= 0:
            logger.error(
                f"Calculated SL value per lot is zero or negative ({sl_value_per_lot:.4f})."
            )
            return 0.0

        # 4. Calculate the final lot size
        lot_size = risk_amount / sl_value_per_lot
        final_lot_size = normalize_lot(symbol, lot_size)

        logger.info(
            f"Calc: Balance={account_balance:,.2f}, Risk={risk_percent}%, SL={sl_pips} pips, Symbol={symbol}"
        )
        logger.info(
            f" -> Risk Amount={risk_amount:,.2f}, Value per Pip/Lot={value_per_pip:,.2f}"
        )
        logger.info(
            f" -> SL Value/Lot={sl_value_per_lot:,.2f}, Raw Lot={lot_size:.4f} -> Normalized Lot={final_lot_size}"
        )

        return final_lot_size

    def calculate_rr(
        self, symbol: str, entry_price: float, sl_price: float, tp_price: float
    ) -> float:
        """
        Calculates the risk-to-reward ratio of a trade.

        Args:
            symbol (str): The trade's symbol.
            entry_price (float): The entry price.
            sl_price (float): The stop loss price.
            tp_price (float): The take profit price.

        Returns:
            float: The reward ratio (e.g., 2.5 for a 1:2.5 R:R). Returns 0.0 if SL is invalid.
        """
        if sl_price == 0.0 or tp_price == 0.0:
            logger.warning("SL or TP price is zero, cannot calculate R:R.")
            return 0.0

        risk_pips = calculate_pips(symbol, entry_price, sl_price)
        reward_pips = calculate_pips(symbol, entry_price, tp_price)

        if risk_pips <= 0:
            logger.error(
                "Risk (pips from entry to SL) is zero or negative. Cannot calculate R:R."
            )
            return 0.0

        rr_ratio = reward_pips / risk_pips

        logger.info(
            f"R:R Calc: Risk={risk_pips:.1f} pips, Reward={reward_pips:.1f} pips -> Ratio=1:{rr_ratio:.2f}"
        )

        return rr_ratio


# --- Singleton Factory ---
_trade_calculator = None


def get_trade_calculator():
    """Factory function to get the singleton TradeCalculator instance."""
    global _trade_calculator
    if _trade_calculator is None:
        _trade_calculator = TradeCalculator()
    return _trade_calculator
