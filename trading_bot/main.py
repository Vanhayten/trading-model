from trading_bot import TradingBot
import MetaTrader5 as mt5

mt5.initialize()
login = 68166696
password = "Developper@1996"
server = "RoboForex-Pro"
mt5.login(login, password, server)

if __name__ == "__main__":
    symbol = "XAUUSD"
    timeframe = mt5.TIMEFRAME_M5
    prompt_template = """
**Scalping Trading Decision Generation Prompt**

**Task:** Generate a scalping trading decision based on the provided 5-minute candlestick data for XAUUSD, including a buy/sell signal, stop-loss level, take-profit level, and an explanation for the decision.

**Input:**

*   **Symbol:** XAUUSD (Gold vs. US Dollar)
*   **Timeframe:** 5-minute
*   **Candlestick Data:**
{data}

**Output:**

*   **Signal:** <buy/sell>
*   **Stop-Loss:** <stop-loss level>
*   **Take-Profit:** <take-profit level>
*   **Explanation:** <explanation for the decision>

**Examples:**

Example 1:
**Signal:** Buy
**Stop-Loss:** 2405.50
**Take-Profit:** 2410.75
**Explanation:** The price of XAUUSD has been in an uptrend, ...

Example 2:
**Signal:** Sell
**Stop-Loss:** 2398.25
**Take-Profit:** 2390.50
**Explanation:** The price of XAUUSD has formed a double top pattern, ...

**Requirements:**

*   Analyze the provided 5-minute candlestick data for XAUUSD using technical indicators and algorithms suitable for scalping.
*   Generate a scalping trading decision based on the analysis, including a buy/sell signal, stop-loss level, and take-profit level.
*   Provide an explanation for the trading decision based on the analysis of the candlestick data and technical indicators.
*   Consider the following scalping parameters:
    *   Trade duration: 15-30 minutes
    *   Stop-loss: 2-5 pips
    *   Take-profit: 2-5 pips
*   Provide a clear and concise output, including the signal, stop-loss, take-profit levels, and explanation.
*   Prioritize trade setups with higher probability and risk-reward ratios.
*   Utilize additional technical indicators or chart patterns for enhanced decision-making.
"""

    trading_bot = TradingBot(symbol, timeframe, prompt_template)
    trading_bot.run()