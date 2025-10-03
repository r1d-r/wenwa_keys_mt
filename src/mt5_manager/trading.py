"""
Trading operations for MetaTrader 5.
Handles order placement, modification, and execution.
"""

import MetaTrader5 as mt5
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from src.config.logger import get_logger
from src.config.settings import get_settings
from src.mt5_manager.connection import get_connection
from src.mt5_manager.utils import (
    normalize_price, normalize_lot, get_current_bid, get_current_ask,
    is_buy_order, is_sell_order, get_order_type_string
)

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class OrderResult:
    """Result of an order operation."""
    success: bool
    order_ticket: Optional[int] = None
    deal_ticket: Optional[int] = None
    volume: Optional[float] = None
    price: Optional[float] = None
    comment: Optional[str] = None
    error_code: Optional[int] = None
    error_description: Optional[str] = None
    retcode: Optional[int] = None
    retcode_description: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of order result."""
        if self.success:
            return (f"✓ Order #{self.order_ticket} executed: "
                   f"{self.volume} lots @ {self.price}")
        else:
            return (f"✗ Order failed: {self.error_description} "
                   f"(Code: {self.error_code}, Retcode: {self.retcode})")


class TradingManager:
    """Manages trading operations."""
    
    def __init__(self):
        """Initialize trading manager."""
        self.conn = get_connection()
        self.default_magic = 234000  # Default magic number for Magic Keys
        self.default_deviation = settings.get_int('Trading', 'max_slippage', 5)
    
    def place_market_order(self,
                          symbol: str,
                          order_type: int,
                          volume: float,
                          sl: float = 0.0,
                          tp: float = 0.0,
                          comment: str = "",
                          magic: Optional[int] = None,
                          deviation: Optional[int] = None) -> OrderResult:
        """
        Place a market order (buy or sell).
        
        Args:
            symbol: Symbol to trade
            order_type: mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL
            volume: Volume in lots
            sl: Stop loss price (0 = no stop loss)
            tp: Take profit price (0 = no take profit)
            comment: Order comment
            magic: Magic number (uses default if None)
            deviation: Maximum price deviation in points
            
        Returns:
            OrderResult object with execution details
        """
        if not self.conn.is_connected():
            logger.error("Not connected to MT5")
            return OrderResult(
                success=False,
                error_description="Not connected to MT5"
            )
        
        # Use defaults if not provided
        if magic is None:
            magic = self.default_magic
        if deviation is None:
            deviation = self.default_deviation
        
        # Validate and normalize inputs
        volume = normalize_lot(symbol, volume)
        if sl != 0.0:
            sl = normalize_price(symbol, sl)
        if tp != 0.0:
            tp = normalize_price(symbol, tp)
        
        # Get current price
        if order_type == mt5.ORDER_TYPE_BUY:
            price = get_current_ask(symbol)
        else:
            price = get_current_bid(symbol)
        
        if price is None:
            logger.error(f"Cannot get price for {symbol}")
            return OrderResult(
                success=False,
                error_description=f"Cannot get price for {symbol}"
            )
        
        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._get_filling_mode(symbol),
        }
        
        # Log order attempt
        order_type_str = get_order_type_string(order_type)
        logger.info(f"Placing {order_type_str} order: {volume} {symbol} @ {price}")
        if sl != 0.0:
            logger.info(f"  SL: {sl}")
        if tp != 0.0:
            logger.info(f"  TP: {tp}")
        
        # Send order
        result = mt5.order_send(request)
        
        # Process result
        return self._process_order_result(result, request)
    
    def buy(self,
            symbol: str,
            volume: float,
            sl: float = 0.0,
            tp: float = 0.0,
            comment: str = "Magic Keys Buy",
            magic: Optional[int] = None) -> OrderResult:
        """
        Place a market buy order.
        
        Args:
            symbol: Symbol to trade
            volume: Volume in lots
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            magic: Magic number
            
        Returns:
            OrderResult object
        """
        return self.place_market_order(
            symbol=symbol,
            order_type=mt5.ORDER_TYPE_BUY,
            volume=volume,
            sl=sl,
            tp=tp,
            comment=comment,
            magic=magic
        )
    
    def sell(self,
             symbol: str,
             volume: float,
             sl: float = 0.0,
             tp: float = 0.0,
             comment: str = "Magic Keys Sell",
             magic: Optional[int] = None) -> OrderResult:
        """
        Place a market sell order.
        
        Args:
            symbol: Symbol to trade
            volume: Volume in lots
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            magic: Magic number
            
        Returns:
            OrderResult object
        """
        return self.place_market_order(
            symbol=symbol,
            order_type=mt5.ORDER_TYPE_SELL,
            volume=volume,
            sl=sl,
            tp=tp,
            comment=comment,
            magic=magic
        )
    
    def instant_buy(self, symbol: str, volume: float = 0.01) -> OrderResult:
        """
        Quick buy at market price (FN1 button functionality).
        
        Args:
            symbol: Symbol to trade
            volume: Volume in lots (default: 0.01)
            
        Returns:
            OrderResult object
        """
        logger.info(f"INSTANT BUY: {volume} {symbol}")
        return self.buy(symbol, volume, comment="Magic Keys Instant Buy")
    
    def instant_sell(self, symbol: str, volume: float = 0.01) -> OrderResult:
        """
        Quick sell at market price (FN2 button functionality).
        
        Args:
            symbol: Symbol to trade
            volume: Volume in lots (default: 0.01)
            
        Returns:
            OrderResult object
        """
        logger.info(f"INSTANT SELL: {volume} {symbol}")
        return self.sell(symbol, volume, comment="Magic Keys Instant Sell")
    
    def close_position(self,
                       ticket: int,
                       volume: Optional[float] = None,
                       comment: str = "Magic Keys Close") -> OrderResult:
        """
        Close a position (full or partial).
        
        Args:
            ticket: Position ticket to close
            volume: Volume to close (None = close all)
            comment: Close comment
            
        Returns:
            OrderResult object
        """
        if not self.conn.is_connected():
            logger.error("Not connected to MT5")
            return OrderResult(
                success=False,
                error_description="Not connected to MT5"
            )
        
        # Get position info
        from src.mt5_manager.positions import get_position_manager
        pm = get_position_manager()
        position = pm.get_position_by_ticket(ticket)
        
        if position is None:
            logger.error(f"Position #{ticket} not found")
            return OrderResult(
                success=False,
                error_description=f"Position #{ticket} not found"
            )
        
        # Determine volume to close
        if volume is None:
            volume = position.volume
        else:
            volume = min(volume, position.volume)
            volume = normalize_lot(position.symbol, volume)
        
        # Determine order type (opposite of position type)
        if position.is_buy():
            close_type = mt5.ORDER_TYPE_SELL
            price = get_current_bid(position.symbol)
        else:
            close_type = mt5.ORDER_TYPE_BUY
            price = get_current_ask(position.symbol)
        
        if price is None:
            logger.error(f"Cannot get price for {position.symbol}")
            return OrderResult(
                success=False,
                error_description=f"Cannot get price for {position.symbol}"
            )
        
        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": self.default_deviation,
            "magic": position.magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._get_filling_mode(position.symbol),
        }
        
        # Log close attempt
        logger.info(f"Closing position #{ticket}: {volume}/{position.volume} lots of {position.symbol}")
        
        # Send close request
        result = mt5.order_send(request)
        
        # Process result
        return self._process_order_result(result, request)
    
    def close_position_full(self, ticket: int) -> OrderResult:
        """
        Close a position completely (CLOSE FULL button).
        
        Args:
            ticket: Position ticket to close
            
        Returns:
            OrderResult object
        """
        logger.info(f"CLOSE FULL: Position #{ticket}")
        return self.close_position(ticket, comment="Magic Keys Close Full")
    
    def close_position_half(self, ticket: int) -> OrderResult:
        """
        Close half of a position (CLOSE HALF button).
        
        Args:
            ticket: Position ticket to close
            
        Returns:
            OrderResult object
        """
        from src.mt5_manager.positions import get_position_manager
        pm = get_position_manager()
        position = pm.get_position_by_ticket(ticket)
        
        if position is None:
            return OrderResult(
                success=False,
                error_description=f"Position #{ticket} not found"
            )
        
        half_volume = position.volume / 2.0
        half_volume = normalize_lot(position.symbol, half_volume)
        
        logger.info(f"CLOSE HALF: Position #{ticket} - {half_volume} lots")
        return self.close_position(ticket, volume=half_volume, comment="Magic Keys Close Half")
    
    def close_position_custom(self, ticket: int, percentage: float = 25.0) -> OrderResult:
        """
        Close a custom percentage of a position (CLOSE CUSTOM button).
        
        Args:
            ticket: Position ticket to close
            percentage: Percentage to close (default: 25%)
            
        Returns:
            OrderResult object
        """
        from src.mt5_manager.positions import get_position_manager
        pm = get_position_manager()
        position = pm.get_position_by_ticket(ticket)
        
        if position is None:
            return OrderResult(
                success=False,
                error_description=f"Position #{ticket} not found"
            )
        
        # Calculate volume
        custom_volume = position.volume * (percentage / 100.0)
        custom_volume = normalize_lot(position.symbol, custom_volume)
        
        logger.info(f"CLOSE CUSTOM: Position #{ticket} - {percentage}% ({custom_volume} lots)")
        return self.close_position(ticket, volume=custom_volume, 
                                   comment=f"Magic Keys Close {percentage}%")
    
    def close_all_positions(self, symbol: str) -> Dict[int, OrderResult]:
        """
        Close all positions for a symbol.
        
        Args:
            symbol: Symbol to close all positions for
            
        Returns:
            Dictionary mapping ticket to OrderResult
        """
        from src.mt5_manager.positions import get_position_manager
        pm = get_position_manager()
        
        positions = pm.get_positions_by_symbol(symbol)
        
        if not positions:
            logger.warning(f"No positions found for {symbol}")
            return {}
        
        logger.info(f"Closing {len(positions)} positions for {symbol}")
        
        results = {}
        for position in positions:
            result = self.close_position_full(position.ticket)
            results[position.ticket] = result
        
        return results
    
    def close_symbol_full(self, symbol: str) -> Dict[int, OrderResult]:
        """
        Close all positions for a symbol (CLOSE FULL on symbol).
        
        Args:
            symbol: Symbol to close
            
        Returns:
            Dictionary mapping ticket to OrderResult
        """
        logger.info(f"CLOSE FULL for {symbol}")
        return self.close_all_positions(symbol)
    
    def close_symbol_half(self, symbol: str) -> Dict[int, OrderResult]:
        """
        Close half of all positions for a symbol (CLOSE HALF on symbol).
        
        Args:
            symbol: Symbol to close
            
        Returns:
            Dictionary mapping ticket to OrderResult
        """
        from src.mt5_manager.positions import get_position_manager
        pm = get_position_manager()
        
        positions = pm.get_positions_by_symbol(symbol)
        
        if not positions:
            logger.warning(f"No positions found for {symbol}")
            return {}
        
        logger.info(f"CLOSE HALF for {symbol} - {len(positions)} positions")
        
        results = {}
        for position in positions:
            result = self.close_position_half(position.ticket)
            results[position.ticket] = result
        
        return results
    
    def close_symbol_custom(self, symbol: str, percentage: float = 25.0) -> Dict[int, OrderResult]:
        """
        Close custom percentage of all positions for a symbol.
        
        Args:
            symbol: Symbol to close
            percentage: Percentage to close (default: 25%)
            
        Returns:
            Dictionary mapping ticket to OrderResult
        """
        from src.mt5_manager.positions import get_position_manager
        pm = get_position_manager()
        
        positions = pm.get_positions_by_symbol(symbol)
        
        if not positions:
            logger.warning(f"No positions found for {symbol}")
            return {}
        
        logger.info(f"CLOSE CUSTOM {percentage}% for {symbol} - {len(positions)} positions")
        
        results = {}
        for position in positions:
            result = self.close_position_custom(position.ticket, percentage)
            results[position.ticket] = result
        
        return results
    
    def _get_filling_mode(self, symbol: str) -> int:
        """
        Get appropriate filling mode for the symbol.
        
        Args:
            symbol: Symbol name
            
        Returns:
            Filling mode constant
        """
        symbol_info = self.conn.get_symbol_info(symbol)
        
        if symbol_info is None:
            logger.warning(f"Cannot get filling mode for {symbol}, using FOK")
            return mt5.ORDER_FILLING_FOK
        
        # Get filling mode from symbol
        filling_mode = symbol_info.filling_mode
        
        # Check allowed filling modes (using bitmask operations)
        if filling_mode & 1:
            return mt5.ORDER_FILLING_FOK
        elif filling_mode & 2:
            return mt5.ORDER_FILLING_IOC
        elif filling_mode & 4:
            return mt5.ORDER_FILLING_RETURN
        
        logger.warning(f"No filling mode found for {symbol}, defaulting to FOK")
        return mt5.ORDER_FILLING_FOK
    
    def _process_order_result(self, result, request: Dict) -> OrderResult:
        """
        Process MT5 order result.
        
        Args:
            result: MT5 order result object
            request: Original order request
            
        Returns:
            OrderResult object
        """
        if result is None:
            error = mt5.last_error()
            logger.error(f"Order failed: {error}")
            return OrderResult(
                success=False,
                error_code=error[0],
                error_description=error[1]
            )
        
        # Get retcode description
        retcode_dict = {
            mt5.TRADE_RETCODE_DONE: "Request completed",
            mt5.TRADE_RETCODE_PLACED: "Order placed",
            mt5.TRADE_RETCODE_DONE_PARTIAL: "Partial execution",
            mt5.TRADE_RETCODE_ERROR: "Request processing error",
            mt5.TRADE_RETCODE_TIMEOUT: "Request timeout",
            mt5.TRADE_RETCODE_INVALID: "Invalid request",
            mt5.TRADE_RETCODE_INVALID_VOLUME: "Invalid volume",
            mt5.TRADE_RETCODE_INVALID_PRICE: "Invalid price",
            mt5.TRADE_RETCODE_INVALID_STOPS: "Invalid stops",
            mt5.TRADE_RETCODE_TRADE_DISABLED: "Trade disabled",
            mt5.TRADE_RETCODE_MARKET_CLOSED: "Market closed",
            mt5.TRADE_RETCODE_NO_MONEY: "Insufficient funds",
            mt5.TRADE_RETCODE_PRICE_CHANGED: "Price changed",
            mt5.TRADE_RETCODE_PRICE_OFF: "No prices",
            mt5.TRADE_RETCODE_INVALID_EXPIRATION: "Invalid expiration",
            mt5.TRADE_RETCODE_ORDER_CHANGED: "Order changed",
            mt5.TRADE_RETCODE_TOO_MANY_REQUESTS: "Too many requests",
            mt5.TRADE_RETCODE_NO_CHANGES: "No changes",
            mt5.TRADE_RETCODE_SERVER_DISABLES_AT: "Autotrading disabled by server",
            mt5.TRADE_RETCODE_CLIENT_DISABLES_AT: "Autotrading disabled by client",
            mt5.TRADE_RETCODE_LOCKED: "Request locked",
            mt5.TRADE_RETCODE_FROZEN: "Order/position frozen",
            mt5.TRADE_RETCODE_INVALID_FILL: "Invalid fill type",
            mt5.TRADE_RETCODE_CONNECTION: "No connection",
            mt5.TRADE_RETCODE_ONLY_REAL: "Only real accounts allowed",
            mt5.TRADE_RETCODE_LIMIT_ORDERS: "Orders limit reached",
            mt5.TRADE_RETCODE_LIMIT_VOLUME: "Volume limit reached",
        }
        
        retcode_desc = retcode_dict.get(result.retcode, f"Unknown retcode: {result.retcode}")
        
        # Check if order was successful
        success = result.retcode in [
            mt5.TRADE_RETCODE_DONE,
            mt5.TRADE_RETCODE_PLACED,
            mt5.TRADE_RETCODE_DONE_PARTIAL
        ]
        
        if success:
            logger.info(f"✓ Order executed successfully: #{result.order}")
            logger.info(f"  Volume: {result.volume}")
            logger.info(f"  Price: {result.price}")
            if result.comment:
                logger.info(f"  Comment: {result.comment}")
        else:
            logger.error(f"✗ Order failed: {retcode_desc}")
            if result.comment:
                logger.error(f"  Server comment: {result.comment}")
        
        return OrderResult(
            success=success,
            order_ticket=result.order,
            deal_ticket=result.deal,
            volume=result.volume,
            price=result.price,
            comment=result.comment,
            retcode=result.retcode,
            retcode_description=retcode_desc
        )
    
    def validate_order(self,
                       symbol: str,
                       order_type: int,
                       volume: float,
                       sl: float = 0.0,
                       tp: float = 0.0) -> Tuple[bool, str]:
        """
        Validate order parameters before execution.
        
        Args:
            symbol: Symbol to trade
            order_type: Order type
            volume: Volume in lots
            sl: Stop loss price
            tp: Take profit price
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check connection
        if not self.conn.is_connected():
            return False, "Not connected to MT5"
        
        # Get symbol info
        symbol_info = self.conn.get_symbol_info(symbol)
        if symbol_info is None:
            return False, f"Symbol {symbol} not found"
        
        # Check if trading is allowed
        if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
            return False, f"Trading not allowed for {symbol}"
        
        # Check volume
        if volume < symbol_info.volume_min:
            return False, f"Volume {volume} below minimum {symbol_info.volume_min}"
        
        if volume > symbol_info.volume_max:
            return False, f"Volume {volume} exceeds maximum {symbol_info.volume_max}"
        
        # Check stops if provided
        if sl != 0.0 or tp != 0.0:
            stops_level = symbol_info.trade_stops_level * symbol_info.point
            
            if is_buy_order(order_type):
                current_price = get_current_ask(symbol)
                if sl != 0.0 and (current_price - sl) < stops_level:
                    return False, f"Stop loss too close to market (min distance: {stops_level})"
                if tp != 0.0 and (tp - current_price) < stops_level:
                    return False, f"Take profit too close to market (min distance: {stops_level})"
            else:
                current_price = get_current_bid(symbol)
                if sl != 0.0 and (sl - current_price) < stops_level:
                    return False, f"Stop loss too close to market (min distance: {stops_level})"
                if tp != 0.0 and (current_price - tp) < stops_level:
                    return False, f"Take profit too close to market (min distance: {stops_level})"
        
        # Check account balance
        account_info = self.conn.get_account_info()
        if account_info and account_info.margin_free <= 0:
            return False, "Insufficient free margin"
        
        return True, "Order validation passed"


# Global trading manager instance
trading_manager = TradingManager()


def get_trading_manager() -> TradingManager:
    """
    Get the global trading manager instance.
    
    Returns:
        TradingManager: Global trading manager object
    """
    return trading_manager
