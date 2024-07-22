from datetime import datetime
import pandas as pd
from enum import Enum

class Timeframe(Enum):
    M1 = 1
    M5 = 5
    M15 = 15
    M30 = 30
    H1 = 60
    H4 = 240
    D1 = 1440

# Calculate dates
today = datetime.now()
end_date = today
start_date = today - pd.DateOffset(months=3)  # Use pandas DateOffset to subtract months

# Convert dates to strings for config
BACKTESTING_START_DATE = start_date.strftime('%Y-%m-%d')
BACKTESTING_END_DATE = end_date.strftime('%Y-%m-%d')

CONFIG = {
    'MT5_LOGIN': 68166696,
    'MT5_PASSWORD': 'Developper@1996',
    'MT5_SERVER': 'RoboForex-Pro',
    'SYMBOL': 'XAUUSD',
    'TIMEFRAME': Timeframe.M5,
    'LLM_API_URL': 'https://api.openai.com/v1/chat/completions',
    'LLM_API_KEY': 'sk-proj-qsjsHysXG4nocUyRtTBJT3BlbkFJZcRnoM3JgiXnXXrZhR4x',
    #'LLM_API_KEY': 'sk-proj-qsjsHysXG4nocUyRtTBJT3BlbkFJZcRnoM3JgiXnXXrZhR4x-test',
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 5,
    'MAX_RISK_PER_TRADE': 0.01,
    'BACKTESTING_START_DATE': BACKTESTING_START_DATE,
    'BACKTESTING_END_DATE': BACKTESTING_END_DATE
}