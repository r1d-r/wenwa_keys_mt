# Magic Keys MT5 Trading Manager - Master Checklist

## Phase 1: Project Setup & Environment

- [x] Create project directory structure
- [x] Set up Python virtual environment
- [x] Install required dependencies (MetaTrader5, tkinter, configparser, logging)
- [x] Create requirements.txt file
- [x] Set up logging configuration
- [x] Create configuration file structure (config.ini)
- [x] Initialize Git repository (optional but recommended)

## Phase 2: MetaTrader 5 Integration Core

- [ ] Create MT5 connection module
- [ ] Implement MT5 authentication and initialization
- [ ] Create utility functions for symbol info retrieval
- [ ] Implement account information retrieval
- [ ] Create position management functions (get all positions, get positions by symbol)
- [ ] Implement order placement functions (market orders)
- [ ] Implement pending order placement functions
- [ ] Create position closing functions (full, partial, by ticket)
- [ ] Implement stop loss modification functions
- [ ] Implement take profit modification functions
- [ ] Create pip calculation utilities
- [ ] Implement lot size calculator based on risk %
- [ ] Add error handling and connection recovery

## Phase 3: Trade Calculator Module

- [ ] Create TradeCalculator class
- [ ] Implement risk calculation logic (% of balance)
- [ ] Implement lot size calculation from risk and SL distance
- [ ] Implement risk:reward ratio calculations
- [ ] Create price level validation functions
- [ ] Implement pip distance calculations
- [ ] Add support for different account currencies
- [ ] Create function to calculate position value

## Phase 4: Advanced Trading Features

- [ ] Implement Auto Breakeven (BE) trigger system
- [ ] Create Partial Take Profit (PTP) trigger system
- [ ] Implement trigger monitoring background thread
- [ ] Create trigger storage and persistence
- [ ] Implement SL to entry function
- [ ] Create SL to profit function
- [ ] Implement double order functionality
- [ ] Create instant buy/sell functions
- [ ] Add trade selection logic (specific trade vs all trades)

## Phase 5: Chart & Timeframe Management

- [ ] Implement timeframe switching (TF UP/TF DW)
- [ ] Create chart zoom functions
- [ ] Implement current symbol detection
- [ ] Add chart state management

## Phase 6: Statistics & Tracking

- [ ] Create trade statistics tracker
- [ ] Implement win/loss counter
- [ ] Create max pips tracker
- [ ] Implement cumulative risk calculator
- [ ] Create trade count tracker
- [ ] Implement statistics persistence (save/load)
- [ ] Create statistics display formatter

## Phase 7: Python GUI - Layout & Structure

- [ ] Create main application window with tkinter
- [ ] Design 6-row × 5-column grid layout
- [ ] Implement Magic Keys branding header
- [ ] Create button base class with styling
- [ ] Implement color scheme (green, yellow, red, gray)
- [ ] Create custom button shapes (tall ENTER button, wide MARKET/PENDING)
- [ ] Add responsive grid sizing
- [ ] Implement dark theme background

## Phase 8: Python GUI - Row 1 (Function Keys)

- [ ] Create Autokey (Menu) toggle button
- [ ] Implement FN 1 (Instant Buy) button
- [ ] Implement FN 2 (Instant Sell) button
- [ ] Create TF DW (Lower Timeframe) button
- [ ] Create TF UP (Higher Timeframe) button
- [ ] Connect buttons to MT5 functions

## Phase 9: Python GUI - Row 2 (Risk & SL Management)

- [ ] Create PARTIAL SL button with dialog
- [ ] Implement FN button (linkable to Partial SL)
- [ ] Create INPUT RISK button with input dialog
- [ ] Create INPUT PIPS button with input dialog
- [ ] Implement SL in profit button
- [ ] Add input validation for dialogs

## Phase 10: Python GUI - Row 3 (Trading Actions)

- [ ] Create AUTO BE button with trigger setup
- [ ] Implement OPEN CALC button (show calculator overlay)
- [ ] Create OPEN TRADE button
- [ ] Implement DOUBLE ORDER button
- [ ] Create ZOOM OUT button
- [ ] Add confirmation dialogs for critical actions

## Phase 11: Python GUI - Row 4 (Target Management)

- [ ] Create PARTIAL TP button with trigger setup
- [ ] Implement SL @entry button
- [ ] Create TARGET @default button
- [ ] Create TARGET @1:x button with RR input
- [ ] Implement ZOOM IN button
- [ ] Connect target functions to calculator and open trades

## Phase 12: Python GUI - Row 5 (Position Management)

- [ ] Create SELECT button (trade selector)
- [ ] Implement CLOSE FULL button
- [ ] Create CLOSE HALF button
- [ ] Create CLOSE CUSTOM button with % setting
- [ ] Implement tall ENTER button (confirmation)
- [ ] Add visual feedback for selected trades

## Phase 13: Python GUI - Row 6 (Utilities)

- [ ] Create SWITCH button (buy/sell toggle)
- [ ] Implement wide MARKET/PENDING toggle button
- [ ] Create SHOW STATS button with stats overlay
- [ ] Design stats display panel

## Phase 14: Trade Calculator Overlay

- [ ] Create calculator overlay window
- [ ] Implement draggable SL line control
- [ ] Implement draggable TP line control
- [ ] Add entry line for pending orders
- [ ] Display calculated lot size
- [ ] Show risk amount and percentage
- [ ] Display pip distance
- [ ] Add visual indicators on overlay
- [ ] Implement line selection toggle (SELECT button)

## Phase 15: MT5 Expert Advisor (MQL5)

- [ ] Create EA project structure
- [ ] Implement EA input parameters
- [ ] Create connection handler with Python (named pipes/sockets)
- [ ] Implement command receiver
- [ ] Create trade execution functions in EA
- [ ] Implement position modification functions
- [ ] Add Auto BE trigger monitoring
- [ ] Add Partial TP trigger monitoring
- [ ] Create pip tracking display on chart
- [ ] Implement statistics display on chart
- [ ] Add visual indicators for triggers
- [ ] Create EA error handling and logging

## Phase 16: Python-EA Communication Bridge

- [ ] Design communication protocol (JSON commands)
- [ ] Implement named pipe server (Windows) or socket (cross-platform)
- [ ] Create message queue system
- [ ] Implement command serialization
- [ ] Create response handling
- [ ] Add connection monitoring and auto-reconnect
- [ ] Implement heartbeat mechanism
- [ ] Create command acknowledgment system

## Phase 17: Keyboard Integration (Optional Hardware)

- [ ] Research keyboard input libraries (pynput, keyboard)
- [ ] Create keyboard listener module
- [ ] Map physical keys to button functions
- [ ] Implement key combination detection
- [ ] Add keyboard shortcut configuration
- [ ] Create keyboard event handler
- [ ] Add toggle for keyboard vs GUI control

## Phase 18: Settings & Configuration

- [ ] Create settings dialog window
- [ ] Implement default pip distance setting
- [ ] Add custom close percentage setting
- [ ] Create risk percentage default setting
- [ ] Add Auto BE trigger offset setting
- [ ] Implement Partial TP percentage settings
- [ ] Create color theme customization
- [ ] Add hotkey mapping configuration
- [ ] Implement settings save/load functionality

## Phase 19: Testing & Validation

- [ ] Test MT5 connection on demo account
- [ ] Test market order execution
- [ ] Test pending order execution
- [ ] Validate lot size calculations
- [ ] Test position closing (full, half, custom)
- [ ] Test SL/TP modifications
- [ ] Validate Auto BE triggers
- [ ] Validate Partial TP triggers
- [ ] Test statistics tracking accuracy
- [ ] Test GUI responsiveness
- [ ] Test error handling scenarios
- [ ] Validate pip calculations across different instruments
- [ ] Test with different account types (hedge/netting)

## Phase 20: Documentation

- [ ] Create README.md with project overview
- [ ] Write installation instructions
- [ ] Document MT5 EA installation steps
- [ ] Create configuration guide
- [ ] Write user manual for each button function
- [ ] Document keyboard shortcuts
- [ ] Create troubleshooting guide
- [ ] Add code comments and docstrings
- [ ] Create API documentation for modules
- [ ] Write developer notes for future enhancements

## Phase 21: Code Cleanup & Optimization

- [ ] Refactor duplicate code into utilities
- [ ] Optimize trigger checking performance
- [ ] Add type hints throughout codebase
- [ ] Implement proper exception handling
- [ ] Review and optimize imports
- [ ] Add unit tests for critical functions
- [ ] Perform code linting (pylint/flake8)
- [ ] Review memory usage and optimize
- [ ] Add code formatting (black/autopep8)
- [ ] Create build/deployment script

## Phase 22: Final Polish & Deployment

- [ ] Create application icon
- [ ] Add splash screen (optional)
- [ ] Implement about dialog
- [ ] Add version checking
- [ ] Create installer/executable (PyInstaller)
- [ ] Write release notes
- [ ] Create demo video/screenshots
- [ ] Final testing on clean environment
- [ ] Package EA and Python app together
- [ ] Create backup and restore functionality
