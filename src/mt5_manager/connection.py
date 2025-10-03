"""
MetaTrader 5 connection manager.
Handles connection, authentication, and state management for MT5 terminal.
"""

import MetaTrader5 as mt5
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import time
from src.config.logger import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class MT5ConnectionError(Exception):
    """Custom exception for MT5 connection errors."""
    pass


class MT5Connection:
    """Manages connection to MetaTrader 5 terminal."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure one MT5 connection."""
        if cls._instance is None:
            cls._instance = super(MT5Connection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize MT5 connection manager."""
        if not MT5Connection._initialized:
            self.connected = False
            self.account_info = None
            self.terminal_info = None
            self.last_error = None
            MT5Connection._initialized = True
    
    def initialize(self, login: Optional[int] = None, 
                   password: Optional[str] = None, 
                   server: Optional[str] = None,
                   timeout: int = 60000,
                   portable: bool = False) -> bool:
        """
        Initialize connection to MT5 terminal.
        
        Args:
            login: MT5 account number (optional if already logged in terminal)
            password: MT5 account password
            server: MT5 server name
            timeout: Connection timeout in milliseconds
            portable: Use portable mode
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Initializing MT5 connection...")
            
            # Initialize MT5
            if not mt5.initialize(timeout=timeout, portable=portable):
                error = mt5.last_error()
                self.last_error = error
                logger.error(f"MT5 initialization failed: {error}")
                return False
            
            logger.info("MT5 initialized successfully")
            
            # If credentials provided, attempt login
            if login and password and server:
                logger.info(f"Attempting login to account {login} on server {server}...")
                if not mt5.login(login=login, password=password, server=server):
                    error = mt5.last_error()
                    self.last_error = error
                    logger.error(f"MT5 login failed: {error}")
                    mt5.shutdown()
                    return False
                logger.info(f"Successfully logged in to account {login}")
            else:
                logger.info("Using existing MT5 terminal session")
            
            # Verify connection and get account info
            self.account_info = mt5.account_info()
            if self.account_info is None:
                error = mt5.last_error()
                self.last_error = error
                logger.error(f"Failed to retrieve account info: {error}")
                mt5.shutdown()
                return False
            
            # Get terminal info
            self.terminal_info = mt5.terminal_info()
            
            self.connected = True
            self._log_connection_info()
            
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Exception during MT5 initialization: {e}", exc_info=True)
            return False
    
    def _log_connection_info(self):
        """Log connection and account information."""
        if self.account_info:
            logger.info("=" * 80)
            logger.info("MT5 CONNECTION ESTABLISHED")
            logger.info("=" * 80)
            logger.info(f"Account Number: {self.account_info.login}")
            logger.info(f"Account Name: {self.account_info.name}")
            logger.info(f"Server: {self.account_info.server}")
            logger.info(f"Currency: {self.account_info.currency}")
            logger.info(f"Balance: {self.account_info.balance:.2f}")
            logger.info(f"Equity: {self.account_info.equity:.2f}")
            logger.info(f"Margin: {self.account_info.margin:.2f}")
            logger.info(f"Free Margin: {self.account_info.margin_free:.2f}")
            logger.info(f"Leverage: 1:{self.account_info.leverage}")
            logger.info(f"Trade Mode: {self._get_trade_mode_string()}")
            logger.info("=" * 80)
        
        if self.terminal_info:
            logger.info(f"Terminal: {self.terminal_info.name}")
            logger.info(f"Terminal Path: {self.terminal_info.path}")
            logger.info(f"Terminal Build: {self.terminal_info.build}")
    
    def _get_trade_mode_string(self) -> str:
        """Get human-readable trade mode string."""
        if not self.account_info:
            return "Unknown"
        
        trade_mode = self.account_info.trade_mode
        modes = {
            0: "Demo Account",
            1: "Real Account",
            2: "Contest Account"
        }
        return modes.get(trade_mode, f"Unknown ({trade_mode})")
    
    def connect(self, use_config: bool = True) -> bool:
        """
        Connect to MT5 using settings from config or existing session.
        
        Args:
            use_config: If True, use credentials from config file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.connected:
            logger.info("Already connected to MT5")
            return True
        
        if use_config:
            credentials = settings.get_mt5_credentials()
            login = int(credentials['login']) if credentials['login'] else None
            password = credentials['password'] if credentials['password'] else None
            server = credentials['server'] if credentials['server'] else None
            
            if login and password and server:
                logger.info("Using credentials from config file")
                return self.initialize(login, password, server)
            else:
                logger.info("No credentials in config, using existing MT5 session")
                return self.initialize()
        else:
            return self.initialize()
    
    def disconnect(self):
        """Disconnect from MT5 terminal."""
        if self.connected:
            logger.info("Disconnecting from MT5...")
            mt5.shutdown()
            self.connected = False
            self.account_info = None
            self.terminal_info = None
            logger.info("Disconnected from MT5")
    
    def reconnect(self, max_attempts: int = 3) -> bool:
        """
        Attempt to reconnect to MT5.
        
        Args:
            max_attempts: Maximum number of reconnection attempts
            
        Returns:
            bool: True if reconnection successful
        """
        logger.warning("Attempting to reconnect to MT5...")
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Reconnection attempt {attempt}/{max_attempts}")
            
            self.disconnect()
            time.sleep(2)
            
            if self.connect():
                logger.info("Reconnection successful!")
                return True
            
            if attempt < max_attempts:
                wait_time = attempt * 2
                logger.warning(f"Reconnection failed. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        logger.error("All reconnection attempts failed")
        return False
    
    def is_connected(self) -> bool:
        """
        Check if connected to MT5.
        
        Returns:
            bool: True if connected and terminal is active
        """
        if not self.connected:
            return False
        
        # Verify connection is still active
        try:
            account = mt5.account_info()
            if account is None:
                logger.warning("MT5 connection lost")
                self.connected = False
                return False
            return True
        except:
            self.connected = False
            return False
    
    def get_account_info(self) -> Optional[Any]:
        """
        Get current account information.
        
        Returns:
            AccountInfo object or None if not connected
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None
        
        self.account_info = mt5.account_info()
        return self.account_info
    
    def get_terminal_info(self) -> Optional[Any]:
        """
        Get terminal information.
        
        Returns:
            TerminalInfo object or None if not connected
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None
        
        self.terminal_info = mt5.terminal_info()
        return self.terminal_info
    
    def get_symbol_info(self, symbol: str) -> Optional[Any]:
        """
        Get information about a trading symbol.
        
        Args:
            symbol: Symbol name (e.g., "EURUSD")
            
        Returns:
            SymbolInfo object or None if symbol not found
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Symbol {symbol} not found")
            return None
        
        # Make sure symbol is visible in MarketWatch
        if not symbol_info.visible:
            logger.info(f"Enabling symbol {symbol} in MarketWatch")
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to enable symbol {symbol}")
                return None
            symbol_info = mt5.symbol_info(symbol)
        
        return symbol_info
    
    def get_symbol_info_tick(self, symbol: str) -> Optional[Any]:
        """
        Get last tick for a symbol.
        
        Args:
            symbol: Symbol name
            
        Returns:
            Tick object or None
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Failed to get tick for {symbol}")
        
        return tick
    
    def get_last_error(self) -> Tuple[int, str]:
        """
        Get last MT5 error.
        
        Returns:
            Tuple of (error_code, error_description)
        """
        return mt5.last_error()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Global connection instance
connection = MT5Connection()


def get_connection() -> MT5Connection:
    """
    Get the global MT5 connection instance.
    
    Returns:
        MT5Connection: Global connection object
    """
    return connection


# --- Connection Decorator ---
def ensure_connected(func):
    """
    A decorator that ensures the MT5 connection is active before calling a function.
    If disconnected, it will attempt to reconnect.
    """

    def wrapper(*args, **kwargs):
        conn = get_connection()
        if not conn.is_connected():
            logger.warning(
                f"Connection lost before calling '{func.__name__}'. Attempting to reconnect..."
            )
            if not conn.reconnect():
                logger.error(
                    f"Cannot execute '{func.__name__}': MT5 connection is down."
                )
                # We can return a default "failure" object, e.g., an empty list or a failed OrderResult
                # For now, we return None, but this can be customized.
                return None
        return func(*args, **kwargs)

    return wrapper


# Example usage and testing
if __name__ == "__main__":
    print("\nTesting MT5 Connection Manager\n")
    print("=" * 80)
    
    # Test connection
    conn = get_connection()
    
    if conn.connect():
        print("\n✅ Connection successful!")
        
        # Test account info
        account = conn.get_account_info()
        if account:
            print(f"\nAccount Balance: {account.balance:.2f} {account.currency}")
            print(f"Equity: {account.equity:.2f}")
            print(f"Free Margin: {account.margin_free:.2f}")
        
        # Test symbol info
        print("\nTesting symbol info for EURUSD:")
        symbol_info = conn.get_symbol_info("EURUSD")
        if symbol_info:
            print(f"  Symbol: {symbol_info.name}")
            print(f"  Digits: {symbol_info.digits}")
            print(f"  Point: {symbol_info.point:.5f}")  # Fixed: format point value properly
            print(f"  Spread: {symbol_info.spread}")
        
        # Test tick info
        tick = conn.get_symbol_info_tick("EURUSD")
        if tick:
            print(f"  Bid: {tick.bid}")
            print(f"  Ask: {tick.ask}")
            print(f"  Time: {datetime.fromtimestamp(tick.time)}")
        
        # Disconnect
        conn.disconnect()
        print("\n✅ Disconnected successfully")
    else:
        print("\n❌ Connection failed!")
        print(f"Error: {conn.last_error}")
    
    print("\n" + "=" * 80)
