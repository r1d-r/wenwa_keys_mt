# Magic Keys MT5 Trading Manager

A professional trading management system for MetaTrader 5 that provides advanced trade execution, risk management, and automation features through both a Python GUI and physical keyboard interface.

## Features

### 🎯 Core Trading Functions

- **Instant Buy/Sell** - Execute market orders instantly
- **Trade Calculator** - Visual calculator with risk-based lot sizing
- **Smart Position Management** - Close full, half, or custom portions
- **Advanced Order Types** - Market and pending orders support

### 🛡️ Risk Management

- **Dynamic Risk Calculator** - Set custom risk per trade (% or lots)
- **Auto Breakeven** - Automatically move SL to entry when triggered
- **Partial Take Profit** - Multiple partial TP levels with triggers
- **Stop Loss Management** - Quick SL to entry or profit

### 📊 Analysis & Tracking

- **Real-time Statistics** - Track wins, losses, max pips, cumulative risk
- **Trade Selection** - Target specific trades or all positions
- **Pip Distance Tools** - Set targets based on pip distance or R:R ratios

### ⚡ Interface Options

- **Modern GUI** - Intuitive interface matching physical device layout
- **Keyboard Support** - Physical keyboard integration (optional)
- **Visual Calculator** - On-chart calculator with draggable lines

## Installation

### Prerequisites

- Windows OS (for MetaTrader 5)
- Python 3.8 or higher
- MetaTrader 5 installed and configured

### Setup

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/magic_keys_mt5.git
cd magic_keys_mt5
```

2. **Create virtual environment:**

```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure settings:**

- Copy `config/config.example.ini` to `config/config.ini`
- Edit `config/config.ini` with your preferences
- MT5 credentials are optional if using existing terminal session

5. **Run the application:**

```bash
python src/main.py
```

## Project Structure

```
magic_keys_mt5/
├── src/
│   ├── gui/                 # GUI components
│   ├── mt5_manager/         # MT5 integration
│   ├── calculator/          # Risk calculations
│   ├── triggers/            # Auto BE & Partial TP
│   ├── stats/               # Statistics tracking
│   └── config/              # Configuration & logging
├── ea/                      # MT5 Expert Advisor
├── config/                  # Configuration files
├── logs/                    # Application logs
└── data/                    # Stats & trigger data
```

## Configuration

Edit `config/config.ini` to customize:

- MT5 connection settings
- Default risk parameters
- GUI colors and layout
- Trigger settings
- Statistics tracking

## Usage

### Quick Start

1. Launch MetaTrader 5
2. Run the Magic Keys application
3. Use the GUI buttons or keyboard shortcuts

### Key Functions

**Trading:**

- `OPEN CALC` - Open trade calculator
- `OPEN TRADE` - Execute trade
- `FN 1/FN 2` - Instant buy/sell

**Risk Management:**

- `INPUT RISK` - Set custom risk
- `INPUT PIPS` - Set target by pips
- `AUTO BE` - Set breakeven trigger
- `PARTIAL TP` - Set partial profit trigger

**Position Management:**

- `CLOSE FULL/HALF/CUSTOM` - Close positions
- `SL @entry` - Move SL to entry
- `SELECT` - Select specific trade

## Development

### Running Tests

```bash
# Test logger
python test_logger.py

# Test MT5 connection
python -m src.mt5_manager.connection

# Test settings
python -m src.config.settings
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Disclaimer

Trading involves substantial risk of loss. This software is provided for educational and research purposes. Use at your own risk.

---

**Version:** 0.1.0  
**Status:** In Development  
**Last Updated:** October 2025
