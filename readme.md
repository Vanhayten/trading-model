# AI-Powered Algorithmic Trading Bot 🤖📈

![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![MetaTrader5](https://img.shields.io/badge/Platform-MetaTrader%205-orange.svg)
![LLM](https://img.shields.io/badge/AI-OpenAI%20GPT-purple.svg)

## Overview

An intelligent trading system combining technical analysis with Large Language Model (LLM) decision-making for automated financial market trading.

## Key Features ✨

- **Multi-Timeframe Analysis**: Comprehensive market analysis across 1M, 5M, 15M, 30M, 1H, 4H, and 1D timeframes
- **AI-Driven Decision Making**: Powered by OpenAI's GPT-4 for intelligent trading insights
- **Advanced Risk Management**: Multiple safeguards to protect trading capital
- **Real-time Market Execution**: Seamless integration with MetaTrader 5
- **Comprehensive Backtesting**: Robust framework for strategy validation
- **Multi-Asset Support**: Trading across Cryptocurrencies, Forex, and Commodities
- **Intelligent Position Sizing**: Volatility-based position management
- **Dynamic Risk Control**: Adaptive Stop Loss and Take Profit calculations

## Technology Stack 🛠️

| Category | Technologies |
|----------|--------------|
| **Core Language** | Python 3.12 |
| **Trading Platform** | MetaTrader 5 |
| **AI Integration** | OpenAI GPT-4 API |
| **Data Analysis** | Pandas, NumPy |
| **CLI Interface** | Click |
| **Risk Management** | Custom volatility-based algorithms |

## Prerequisites

- Python 3.12+
- MetaTrader 5 account
- OpenAI API Key

## Installation & Setup ⚙️

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-trading-bot.git
cd ai-trading-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration 🔧

### Environment Setup

1. Update `config/settings.py` with your credentials:

```python
CONFIG = {
    'MT5_LOGIN': '... Add your MetaTrader 5 Login ID ...',
    'MT5_PASSWORD': '... Add your MetaTrader 5 Password ...',
    'MT5_SERVER': '... Add your MetaTrader 5 Server ...',
    'LLM_API_KEY': '... Add your OpenAI API Key ...',
}
```

### Security Precautions ⚠️

1. **Never commit sensitive credentials to version control**
2. Add to `.gitignore`:
```
config/settings.py
.env
```

3. Use environment variables or secure secret management


## Usage 🚀

### Live Trading Mode

```bash
python main.py run-live
```

### Backtesting Mode

```bash
python main.py run-backtest
```

### Sample Output

```
Real-time Trading Decisions:
Decision 1:
  Signal: buy
  Stop Loss: 56230.5
  Take Profit: 56845.2
  Explanation: Strong bullish divergence on 5M chart with increasing OBV
```

## Project Structure 📁

```
├── config/              # Configuration settings
├── src/
│   ├── application/     # Core business logic
│   ├── domain/          # Data models and value objects
│   ├── infrastructure/ # External integrations
│   └── presentation/    # CLI interface
├── tests/               # Unit tests
├── main.py              # Entry point
└── requirements.txt     # Dependencies
```

## Risk Management System 🛡️

- **Margin Level Monitoring**
- **Maximum Drawdown Control**: Limited to 5%
- **Volatility-Based Position Sizing**
- **Time-Based Trading Restrictions**
- **Simultaneous Position Limits**
- **Minimum Risk/Reward Ratio**: 1:2

## Disclaimer ⚠️

**IMPORTANT**: This is experimental software for educational purposes only.

- Never risk more than you can afford to lose
- The developers assume no responsibility for financial losses
- Algorithmic trading carries significant financial risk
- Past performance does not guarantee future results

## License 📜

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.  
You're free to:
- Use the code commercially/privately
- Modify and redistribute
- Use for personal learning

*Requirements:*
- Include original license/copyright notice
- Not hold author liable

---

## Contributing 👐

While this is a personal project, constructive contributions are welcome!
**Suggested improvements:**
- Bug fixes
- Documentation enhancements
- Performance optimizations
- Test coverage expansion

**Process:**
1. Open an Issue to discuss changes
2. Fork & clone the repository
3. Create a feature branch
4. Commit changes with clear messages
5. Submit a Pull Request with:
   - Description of changes
   - Before/After comparisons if applicable
   - Updated documentation

---

## Contact 📩

**Let's connect!**
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-%230A66C2.svg)](https://www.linkedin.com/in/chaib-ayoub/)
[![Email](https://img.shields.io/badge/Email-Contact%20Me-%23EA4335.svg)](mailto:ayoub.chaib.dev@hotmail.com)

**For project-specific questions:**
- Open a [GitHub Discussion](https://github.com/Vanhayten/trading-model/discussions)
- Create an [Issue](https://github.com/Vanhayten/trading-model/issues) for bugs/feature requests

**Portfolio Feedback:**
I welcome constructive feedback on implementation details or architecture decisions!