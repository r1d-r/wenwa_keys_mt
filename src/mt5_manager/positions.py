"""
Position management for MetaTrader 5.
Handles retrieving, filtering, and managing open positions.
"""

import MetaTrader5 as mt5
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from src.config.logger import get_logger
from src.mt5_manager.connection import get_connection
from src.mt5_manager.utils import (
    is_buy_order, is_sell_order, get_order_type_string,
    calculate_pips, format_price, format_volume
)

logger = get_logger(__name__)


@dataclass
class PositionInfo:
    """Structured position information."""
    ticket: int
    symbol: str
    type: int
    type_string: str
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    profit_pips: float
    swap: float
    comment: str
    time: datetime
    magic: int
    identifier: int
    
    def is_buy(self) -> bool:
        """Check if position is a buy."""
        return is_buy_order(self.type)
    
    def is_sell(self) -> bool:
        """Check if position is a sell."""
        return is_sell_order(self.type)
    
    def is_profitable(self) -> bool:
        """Check if position is in profit."""
        return self.profit > 0
    
    def is_losing(self) -> bool:
        """Check if position is losing."""
        return self.profit < 0
    
    def is_breakeven(self) -> bool:
        """Check if position is at breakeven."""
        return abs(self.profit) < 0.01
    
    def __str__(self) -> str:
        """String representation of position."""
        return (f"#{self.ticket} {self.type_string} {self.volume} {self.symbol} @ "
                f"{self.price_open:.5f} | Profit: ${self.profit:.2f} ({self.profit_pips:.1f} pips)")


class PositionManager:
    """Manages position operations."""
    
    def __init__(self):
        """Initialize position manager."""
        self.conn = get_connection()
        self.selected_ticket = None
    
    def get_all_positions(self) -> List[PositionInfo]:
        """
        Get all open positions.
        
        Returns:
            List of PositionInfo objects
        """
        if not self.conn.is_connected():
            logger.error("Not connected to MT5")
            return []
        
        positions = mt5.positions_get()
        
        if positions is None:
            logger.debug("No positions found or error retrieving positions")
            return []
        
        position_list = []
        for pos in positions:
            position_list.append(self._convert_to_position_info(pos))
        
        logger.debug(f"Retrieved {len(position_list)} positions")
        return position_list
    
    def get_positions_by_symbol(self, symbol: str) -> List[PositionInfo]:
        """
        Get all positions for a specific symbol.
        
        Args:
            symbol: Symbol name
            
        Returns:
            List of PositionInfo objects for the symbol
        """
        if not self.conn.is_connected():
            logger.error("Not connected to MT5")
            return []
        
        positions = mt5.positions_get(symbol=symbol)
        
        if positions is None:
            logger.debug(f"No positions found for {symbol}")
            return []
        
        position_list = []
        for pos in positions:
            position_list.append(self._convert_to_position_info(pos))
        
        logger.debug(f"Retrieved {len(position_list)} positions for {symbol}")
        return position_list
    
    def get_position_by_ticket(self, ticket: int) -> Optional[PositionInfo]:
        """
        Get a specific position by ticket number.
        
        Args:
            ticket: Position ticket number
            
        Returns:
            PositionInfo object or None if not found
        """
        if not self.conn.is_connected():
            logger.error("Not connected to MT5")
            return None
        
        positions = mt5.positions_get(ticket=ticket)
        
        if positions is None or len(positions) == 0:
            logger.warning(f"Position #{ticket} not found")
            return None
        
        return self._convert_to_position_info(positions[0])
    
    def get_buy_positions(self, symbol: Optional[str] = None) -> List[PositionInfo]:
        """
        Get all buy positions, optionally filtered by symbol.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of buy positions
        """
        if symbol:
            positions = self.get_positions_by_symbol(symbol)
        else:
            positions = self.get_all_positions()
        
        return [pos for pos in positions if pos.is_buy()]
    
    def get_sell_positions(self, symbol: Optional[str] = None) -> List[PositionInfo]:
        """
        Get all sell positions, optionally filtered by symbol.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of sell positions
        """
        if symbol:
            positions = self.get_positions_by_symbol(symbol)
        else:
            positions = self.get_all_positions()
        
        return [pos for pos in positions if pos.is_sell()]
    
    def get_profitable_positions(self, symbol: Optional[str] = None) -> List[PositionInfo]:
        """
        Get all profitable positions.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of profitable positions
        """
        if symbol:
            positions = self.get_positions_by_symbol(symbol)
        else:
            positions = self.get_all_positions()
        
        return [pos for pos in positions if pos.is_profitable()]
    
    def get_losing_positions(self, symbol: Optional[str] = None) -> List[PositionInfo]:
        """
        Get all losing positions.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of losing positions
        """
        if symbol:
            positions = self.get_positions_by_symbol(symbol)
        else:
            positions = self.get_all_positions()
        
        return [pos for pos in positions if pos.is_losing()]
    
    def get_total_profit(self, symbol: Optional[str] = None) -> float:
        """
        Calculate total profit from all positions.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            Total profit in account currency
        """
        if symbol:
            positions = self.get_positions_by_symbol(symbol)
        else:
            positions = self.get_all_positions()
        
        total = sum(pos.profit for pos in positions)
        return round(total, 2)
    
    def get_total_volume(self, symbol: Optional[str] = None) -> float:
        """
        Calculate total volume of all positions.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            Total volume in lots
        """
        if symbol:
            positions = self.get_positions_by_symbol(symbol)
        else:
            positions = self.get_all_positions()
        
        total = sum(pos.volume for pos in positions)
        return round(total, 2)
    
    def has_positions(self, symbol: Optional[str] = None) -> bool:
        """
        Check if there are any open positions.
        
        Args:
            symbol: Optional symbol to check
            
        Returns:
            True if positions exist
        """
        if symbol:
            positions = self.get_positions_by_symbol(symbol)
        else:
            positions = self.get_all_positions()
        
        return len(positions) > 0
    
    def select_position(self, ticket: int) -> bool:
        """
        Select a position for targeted operations.
        
        Args:
            ticket: Position ticket to select
            
        Returns:
            True if selection successful
        """
        position = self.get_position_by_ticket(ticket)
        if position:
            self.selected_ticket = ticket
            logger.info(f"Selected position #{ticket}")
            return True
        
        logger.warning(f"Cannot select position #{ticket} - not found")
        return False
    
    def deselect_position(self):
        """Deselect the currently selected position."""
        self.selected_ticket = None
        logger.info("Position deselected")
    
    def get_selected_position(self) -> Optional[PositionInfo]:
        """
        Get the currently selected position.
        
        Returns:
            PositionInfo object or None
        """
        if self.selected_ticket is None:
            return None
        
        return self.get_position_by_ticket(self.selected_ticket)
    
    def get_target_positions(self, symbol: str) -> List[PositionInfo]:
        """
        Get target positions for operations.
        If a position is selected, returns only that position.
        Otherwise returns all positions for the symbol.
        
        Args:
            symbol: Symbol to get positions for
            
        Returns:
            List of target positions
        """
        if self.selected_ticket:
            position = self.get_selected_position()
            if position and position.symbol == symbol:
                return [position]
            else:
                logger.warning(f"Selected position is not for {symbol}")
                return []
        
        return self.get_positions_by_symbol(symbol)
    
    def _convert_to_position_info(self, position) -> PositionInfo:
        """
        Convert MT5 position object to PositionInfo dataclass.
        
        Args:
            position: MT5 position object
            
        Returns:
            PositionInfo object
        """
        # Calculate profit in pips
        profit_pips = calculate_pips(
            position.symbol,
            position.price_open,
            position.price_current
        )
        
        # Adjust pip sign based on position type
        if is_sell_order(position.type):
            if position.price_current > position.price_open:
                profit_pips = -profit_pips
        else:
            if position.price_current < position.price_open:
                profit_pips = -profit_pips
        
        return PositionInfo(
            ticket=position.ticket,
            symbol=position.symbol,
            type=position.type,
            type_string=get_order_type_string(position.type),
            volume=position.volume,
            price_open=position.price_open,
            price_current=position.price_current,
            sl=position.sl,
            tp=position.tp,
            profit=position.profit,
            profit_pips=profit_pips,
            swap=position.swap,
            comment=position.comment,
            time=datetime.fromtimestamp(position.time),
            magic=position.magic,
            identifier=position.identifier
        )
    
    def print_position_summary(self, symbol: Optional[str] = None):
        """
        Print a summary of positions to console.
        
        Args:
            symbol: Optional symbol to filter by
        """
        if symbol:
            positions = self.get_positions_by_symbol(symbol)
            header = f"Positions for {symbol}"
        else:
            positions = self.get_all_positions()
            header = "All Positions"
        
        print("\n" + "=" * 100)
        print(f"{header} ({len(positions)} positions)")
        print("=" * 100)
        
        if not positions:
            print("No positions found.")
        else:
            for pos in positions:
                status = "✓" if pos.is_profitable() else "✗" if pos.is_losing() else "="
                selected = " [SELECTED]" if pos.ticket == self.selected_ticket else ""
                print(f"{status} {pos}{selected}")
            
            total_profit = sum(p.profit for p in positions)
            total_volume = sum(p.volume for p in positions)
            print("-" * 100)
            print(f"Total: {len(positions)} positions | Volume: {total_volume:.2f} lots | "
                  f"Profit: ${total_profit:.2f}")
        
        print("=" * 100)


# Global position manager instance
position_manager = PositionManager()


def get_position_manager() -> PositionManager:
    """
    Get the global position manager instance.
    
    Returns:
        PositionManager: Global position manager object
    """
    return position_manager


# Example usage and testing
if __name__ == "__main__":
    print("\nTesting Position Manager\n")
    print("=" * 100)
    
    conn = get_connection()
    if not conn.connect():
        print("❌ Failed to connect to MT5")
        exit(1)
    
    pm = get_position_manager()
    
    # Test 1: Get all positions
    print("\n1. Testing get_all_positions:")
    all_positions = pm.get_all_positions()
    print(f"   Found {len(all_positions)} total positions")
    
    # Test 2: Get positions by symbol
    print("\n2. Testing get_positions_by_symbol:")
    eurusd_positions = pm.get_positions_by_symbol("EURUSD")
    print(f"   Found {len(eurusd_positions)} EURUSD positions")
    
    # Test 3: Filter by type
    print("\n3. Testing position filtering:")
    buy_positions = pm.get_buy_positions()
    sell_positions = pm.get_sell_positions()
    print(f"   Buy positions: {len(buy_positions)}")
    print(f"   Sell positions: {len(sell_positions)}")
    
    # Test 4: Filter by profitability
    print("\n4. Testing profitability filtering:")
    profitable = pm.get_profitable_positions()
    losing = pm.get_losing_positions()
    print(f"   Profitable positions: {len(profitable)}")
    print(f"   Losing positions: {len(losing)}")
    
    # Test 5: Total calculations
    print("\n5. Testing total calculations:")
    total_profit = pm.get_total_profit()
    total_volume = pm.get_total_volume()
    print(f"   Total profit: ${total_profit:.2f}")
    print(f"   Total volume: {total_volume:.2f} lots")
    
    # Test 6: Position selection
    if all_positions:
        print("\n6. Testing position selection:")
        first_ticket = all_positions[0].ticket
        pm.select_position(first_ticket)
        selected = pm.get_selected_position()
        if selected:
            print(f"   Selected: {selected}")
        pm.deselect_position()
    
    # Test 7: Print summary
    print("\n7. Position Summary:")
    pm.print_position_summary()
    
    conn.disconnect()
    print("\n✅ All position manager tests completed!")
