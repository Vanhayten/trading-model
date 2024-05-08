from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd
import time
import ollama
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the prompt template for generating trading decisions
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

# Initialize the MetaTrader5 library and login to the trading account
mt5.initialize()
login = 68166696
password = "Developper@1996"
server = "RoboForex-Pro"
mt5.login(login, password, server)

# Define the symbol and timeframe for data retrieval
symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_M5

# Function to calculate the start date for data retrieval (last two days)
def calculate_date_from():
    today = datetime.now()
    return today - timedelta(days=2)

# Function to fetch historical data within a specified date range
def fetch_data_range(start_date, end_date, num_data_points):
    rates = pd.DataFrame(mt5.copy_rates_range(symbol, timeframe, start_date, end_date))
    rates["time"] = pd.to_datetime(rates["time"], unit="s")
    return rates.tail(num_data_points)


def extract_trading_decisions(messages):
    trading_decisions = []
    for message in messages:
        lines = message.split("\n")
        if len(lines) < 4:
            print("Invalid trading decision format:", message)
            continue

        signal = lines[0].split(": ")[1].strip()
        stop_loss = lines[1].split(": ")[1].strip()
        take_profit = lines[2].split(": ")[1].strip()
        explanation = "\n".join(lines[3:])

        # Convert to JSON format
        trading_decision_json = {
            "signal": signal,
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "explanation": explanation
        }

        trading_decisions.append(trading_decision_json)

    return trading_decisions

def generate_trading_decisions(candlestick_data):
    prompt = prompt_template.format(data=candlestick_data)
    query = f'{prompt}'
    try:
        response = ollama.chat(model='phi3', messages=[{'role': 'user', 'content': query}])
        messages = response['message']['content'].strip().split("\n\n")
        print("initial desission : ", messages)

        trading_decisions = extract_trading_decisions(messages)
        return trading_decisions

    except Exception as e:
        print(f"Error occurred while running ollama: {e}")
        return []


# Function to execute a trade based on the trading decision
def execute_trade(trading_decision_json):
    signal = trading_decision_json["signal"]
    stop_loss = trading_decision_json["stop_loss"]
    take_profit = trading_decision_json["take_profit"]
    explanation = trading_decision_json["explanation"]

    # Implement your trading logic here
    # You can use the MetaTrader5 library to place trades based on the signal, stop_loss, and take-profit levels

    # Example:
    if signal.startswith("Signal: Buy"):
        # Place a buy order
        # Set the stop-loss and take-profit levels
        pass
    elif signal.startswith("Signal: Sell"):
        # Place a sell order
        # Set the stop-loss and take-profit levels
        pass

    print(f"Explanation: {explanation}")


while True:
    # Calculate the start date for the last two days
    date_from = calculate_date_from()

    # Calculate the end date as the current date and time
    date_to = datetime.now()

    # Fetch historical data for the last two days with a specific number of data points
    num_data_points = 500  # You can adjust this number as needed
    latest_data = fetch_data_range(date_from, date_to, num_data_points)

    # Log the fetched data
    logging.info("Fetched Data:")
    logging.info(latest_data)

    # Generate trading decisions using the ollama library
    trading_decisions = generate_trading_decisions(latest_data.to_string(index=False))

    # Check if trading decisions are available and execute trades
    if trading_decisions:
        for trading_decision_json in trading_decisions:
            print("Trading Decision:", json.dumps(trading_decision_json, indent=2))
            execute_trade(trading_decision_json)
    else:
        logging.warning("No trading decisions generated.")

    # Wait for the next 5-minute interval before fetching new data
    logging.info("Waiting for 5 minutes before fetching new data...")
    time.sleep(300)  # Wait for 5 minutes (300 seconds)