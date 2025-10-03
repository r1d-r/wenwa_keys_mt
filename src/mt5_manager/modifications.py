"""
Position modification functions for MetaTrader 5.
Handles SL/TP modifications, breakeven moves, and profit protection.
"""

import MetaTrader5 as mt5
from typing import Optional, Dict, Tuple
from src.config.logger import get_logger
from src.mt5_manager.connection import ensure_connected, get_connection
from src.mt5_manager.utils import normalize_price, pips_to_price, calculate_pips
from src.mt5_manager.trading import OrderResult

logger = get_logger(__name__)


class PositionModifier:
    """Handles position modifications (SL/TP changes)."""

    def __init__(self):
        """Initialize position modifier."""
        self.conn = get_connection()

    @ensure_connected
    def modify_position(self,
                       ticket: int,
                       sl: Optional[float] = None,
                       tp: Optional[float] = None) -> OrderResult:
        """
        Modify stop loss and/or take profit of a position.
        
        Args:
            ticket: Position ticket to modify
            sl: New stop loss price (None = no change)
            tp: New take profit price (None = no change)
            
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

        # Use current values if not specified
        new_sl = sl if sl is not None else position.sl
        new_tp = tp if tp is not None else position.tp

        # Normalize prices
        if new_sl != 0.0:
            new_sl = normalize_price(position.symbol, new_sl)
        if new_tp != 0.0:
            new_tp = normalize_price(position.symbol, new_tp)

        # Prepare modification request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": ticket,
            "sl": new_sl,
            "tp": new_tp,
        }

        # Log modification
        logger.info(f"Modifying position #{ticket} on {position.symbol}")
        if sl is not None:
            logger.info(f"  New SL: {new_sl} (was: {position.sl})")
        if tp is not None:
            logger.info(f"  New TP: {new_tp} (was: {position.tp})")

        # Send modification request
        result = mt5.order_send(request)

        # Process result (reuse from trading module)
        from src.mt5_manager.trading import TradingManager
        tm = TradingManager()
        return tm._process_order_result(result, request)

    def set_sl_to_entry(self, ticket: int) -> OrderResult:
        """
        Move stop loss to entry price (SL @entry button).
        
        Args:
            ticket: Position ticket
            
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

        # Check if position is in profit
        if not position.is_profitable():
            logger.warning(f"Position #{ticket} is not in profit, cannot move SL to entry")
            return OrderResult(
                success=False,
                error_description="Position not in profit"
            )

        # Check if SL is already at or beyond entry
        if position.sl != 0.0:
            if position.is_buy() and position.sl >= position.price_open:
                logger.info(f"SL already at/beyond entry for position #{ticket}")
                return OrderResult(
                    success=False,
                    error_description="SL already at or beyond entry"
                )
            elif position.is_sell() and position.sl <= position.price_open:
                logger.info(f"SL already at/beyond entry for position #{ticket}")
                return OrderResult(
                    success=False,
                    error_description="SL already at or beyond entry"
                )

        logger.info(f"SL @ENTRY: Moving SL to entry for position #{ticket}")
        return self.modify_position(ticket, sl=position.price_open)

    def set_sl_to_profit(self, ticket: int, pips_in_profit: float = 5.0) -> OrderResult:
        """
        Move stop loss into profit territory (SL in profit button).
        
        Args:
            ticket: Position ticket
            pips_in_profit: Pips in profit to set SL (default: 5)
            
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

        # Check if position is in profit
        if not position.is_profitable():
            logger.warning(f"Position #{ticket} is not in profit")
            return OrderResult(
                success=False,
                error_description="Position not in profit"
            )

        # Calculate SL in profit
        if position.is_buy():
            new_sl = pips_to_price(position.symbol, position.price_open, 
                                   pips_in_profit, "up")
        else:
            new_sl = pips_to_price(position.symbol, position.price_open, 
                                   pips_in_profit, "down")

        logger.info(f"SL IN PROFIT: Moving SL {pips_in_profit} pips in profit for #{ticket}")
        return self.modify_position(ticket, sl=new_sl)

    def set_sl_by_pips(self, ticket: int, pips: float) -> OrderResult:
        """
        Set stop loss at a specific pip distance from current price.
        
        Args:
            ticket: Position ticket
            pips: Pip distance for SL
            
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

        # Calculate SL based on position type
        if position.is_buy():
            new_sl = pips_to_price(position.symbol, position.price_current, 
                                   pips, "down")
        else:
            new_sl = pips_to_price(position.symbol, position.price_current, 
                                   pips, "up")

        logger.info(f"Setting SL {pips} pips from current price for #{ticket}")
        return self.modify_position(ticket, sl=new_sl)

    def set_tp_by_pips(self, ticket: int, pips: float) -> OrderResult:
        """
        Set take profit at a specific pip distance from current price.
        
        Args:
            ticket: Position ticket
            pips: Pip distance for TP
            
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

        # Calculate TP based on position type
        if position.is_buy():
            new_tp = pips_to_price(position.symbol, position.price_current, 
                                   pips, "up")
        else:
            new_tp = pips_to_price(position.symbol, position.price_current, 
                                   pips, "down")

        logger.info(f"Setting TP {pips} pips from current price for #{ticket}")
        return self.modify_position(ticket, tp=new_tp)

    def set_tp_by_rr(self, ticket: int, risk_reward: float = 2.0) -> OrderResult:
        """
        Set take profit based on risk:reward ratio.
        
        Args:
            ticket: Position ticket
            risk_reward: Risk:reward ratio (default: 2.0 = 1:2)
            
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

        if position.sl == 0.0:
            logger.error(f"Cannot set TP by R:R - no SL set for position #{ticket}")
            return OrderResult(
                success=False,
                error_description="No stop loss set"
            )

        # Calculate risk in pips
        risk_pips = calculate_pips(position.symbol, position.price_open, position.sl)

        # Calculate reward in pips
        reward_pips = risk_pips * risk_reward

        # Calculate TP price
        if position.is_buy():
            new_tp = pips_to_price(position.symbol, position.price_open, 
                                   reward_pips, "up")
        else:
            new_tp = pips_to_price(position.symbol, position.price_open, 
                                   reward_pips, "down")

        logger.info(f"Setting TP at 1:{risk_reward} R:R for #{ticket} "
                   f"(Risk: {risk_pips:.1f} pips, Reward: {reward_pips:.1f} pips)")
        return self.modify_position(ticket, tp=new_tp)

    def modify_symbol_sl_to_entry(self, symbol: str) -> Dict[int, OrderResult]:
        """
        Move SL to entry for all profitable positions of a symbol.
        
        Args:
            symbol: Symbol to modify
            
        Returns:
            Dictionary mapping ticket to OrderResult
        """
        from src.mt5_manager.positions import get_position_manager
        pm = get_position_manager()

        positions = pm.get_profitable_positions(symbol)

        if not positions:
            logger.warning(f"No profitable positions found for {symbol}")
            return {}

        logger.info(f"Moving SL to entry for {len(positions)} positions on {symbol}")

        results = {}
        for position in positions:
            result = self.set_sl_to_entry(position.ticket)
            results[position.ticket] = result

        return results


# Global position modifier instance
position_modifier = PositionModifier()


def get_position_modifier() -> PositionModifier:
    """
    Get the global position modifier instance.
    
    Returns:
        PositionModifier: Global position modifier object
    """
    return position_modifier
