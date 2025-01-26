from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Calculate dates
today = datetime.now()
end_date = today
start_date = today - pd.DateOffset(months=3)

# Convert dates to strings for config
BACKTESTING_START_DATE = start_date.strftime('%Y-%m-%d')
BACKTESTING_END_DATE = end_date.strftime('%Y-%m-%d')

CONFIG = {

    'MT5_LOGIN': os.getenv('MT5_LOGIN'),
    'MT5_PASSWORD': os.getenv('MT5_PASSWORD'),
    'MT5_SERVER': os.getenv('MT5_SERVER', 'XMGlobal-MT5-7'),
    'LLM_API_KEY': os.getenv('LLM_API_KEY'),
    'SYMBOL': os.getenv('SYMBOL', 'BTCUSD'),

    'TIMEFRAME': 'M5',
    'LLM_API_URL': 'https://api.openai.com/v1/chat/completions',
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 5,
    'MAX_RISK_PER_TRADE': 0.01,
    'BACKTESTING_START_DATE': BACKTESTING_START_DATE,
    'BACKTESTING_END_DATE': BACKTESTING_END_DATE,
    'CYCLE_INTERVAL': 5, # time waiting until next trade
    'MAX_DAILY_TRADES': 5,
    'MIN_MARGIN_LEVEL': 200,  # 200%
    'MAX_SIMULTANEOUS_POSITIONS': 3,
    'MAX_DRAWDOWN': 0.05,  # 5% maximum drawdown
    '5MIN_MAX_VOLATILITY': 0.003,  # 0.2% standard deviation in returns
    '1MIN_MAX_VOLATILITY': 0.005,  # 0.2% standard deviation in returns
    #'NO_TRADE_HOURS': [0, 1, 2, 3, 4, 5, 20, 21, 22, 23],  # Hours when no new trades should be opened
    'NO_TRADE_HOURS': [0, 1, 2, 3, 4, 5],  # Hours when no new trades should be opened
}


# RoboForex trial MT5 ID is: 68166696
#MetaTrader RoboForex-Pro

# XM trial MT5 ID is: 312555310
#MetaTrader XMGlobal-MT5 7


#Bitcoin: BTCUSD
#Ethereum: ETHUSD
#Gold: XAUUSD
#S&P 500 Futures: ES
#EUR/USD: EURUSD
#Silver: XAGUSD
#GBP/USD: GBPUSD
#USD/JPY: USDJPY