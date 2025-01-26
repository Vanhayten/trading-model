import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import time
import logging
from datetime import datetime
from config.settings import CONFIG
from src.domain.value_objects.timeframe import Timeframe


logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def ensure_mt5_connection(self):
        if not mt5.initialize():
            logger.error(f"MetaTrader5 initialization failed: {mt5.last_error()}")
            raise Exception(f"MetaTrader5 initialization failed: {mt5.last_error()}")

        if not mt5.login(CONFIG['MT5_LOGIN'], CONFIG['MT5_PASSWORD'], CONFIG['MT5_SERVER']):
            logger.error(f"MetaTrader5 login failed: {mt5.last_error()}")
            mt5.shutdown()
            raise Exception(f"MetaTrader5 login failed: {mt5.last_error()}")

    def fetch_historical_data(self, timeframe: Timeframe, start_date: datetime, end_date: datetime) -> pd.DataFrame:
            self.ensure_mt5_connection()
            all_data = pd.DataFrame()

            chunk_size = pd.DateOffset(weeks=1)
            current_start_date = start_date

            while current_start_date < end_date:
                current_end_date = min(current_start_date + chunk_size, end_date)
                for attempt in range(CONFIG['MAX_RETRIES']):
                    try:
                        rates = pd.DataFrame(mt5.copy_rates_range(self.symbol, timeframe.value, current_start_date, current_end_date))
                        if not rates.empty:
                            rates["time"] = pd.to_datetime(rates["time"], unit="s")
                            all_data = pd.concat([all_data, rates], ignore_index=True)
                            break
                    except Exception as e:
                        logger.error(f"Attempt {attempt + 1}: {e}")
                    time.sleep(CONFIG['RETRY_DELAY'])
                else:
                    logger.error(f"Failed to fetch rates for period {current_start_date} to {current_end_date} after {CONFIG['MAX_RETRIES']} attempts")

                current_start_date = current_end_date + pd.Timedelta(minutes=5)

            if all_data.empty:
                raise Exception("Failed to fetch rates after multiple attempts")

            return self._add_technical_indicators(all_data)

    def fetch_latest_data(self, timeframe: Timeframe, num_candles: int = 50 , extra_candles: int = 100) -> pd.DataFrame:
        self.ensure_mt5_connection()

        for attempt in range(CONFIG['MAX_RETRIES']):
            try:
                # Fetch the most recent completed candles
                total_candles = num_candles + extra_candles
                rates = mt5.copy_rates_from_pos(self.symbol, timeframe.value, 0, total_candles)
                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')

                    print(f"1.Current time: {datetime.now()} -- 2.MetaTrader server time: {mt5.symbol_info(self.symbol).time}")

                    # Calculate indicators using all fetched data
                    df_with_indicators = self._add_technical_indicators(df)

                    # Return only the required number of candles
                    return df_with_indicators.tail(num_candles)
                else:
                    print("No data received from MetaTrader 5")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} to fetch latest data failed: {e}")
            time.sleep(CONFIG['RETRY_DELAY'])

        raise Exception(f"Failed to fetch latest data after {CONFIG['MAX_RETRIES']} attempts")

    def fetch_current_tick(self) -> pd.Series:
        self.ensure_mt5_connection()

        for attempt in range(CONFIG['MAX_RETRIES']):
            try:
                tick = mt5.symbol_info_tick(self.symbol)
                if tick is not None:
                    spread = tick.ask - tick.bid
                    return pd.Series({
                        'time': datetime.now(),
                        'open': tick.last,
                        'high': tick.last,
                        'low': tick.last,
                        'close': tick.last,
                        'tick_volume': tick.volume,
                        'spread': spread,
                        'real_volume': tick.volume_real
                    })
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} to fetch latest tick failed: {e}")
            time.sleep(CONFIG['RETRY_DELAY'])

        raise Exception(f"Failed to fetch latest tick after {CONFIG['MAX_RETRIES']} attempts")

    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        # Ensure data is sorted by time
        data = data.sort_values('time')

        # Calculate returns
        data['returns'] = data['close'].pct_change()

        # SMA and EMA
        data['SMA_20'] = data['close'].rolling(window=20).mean()
        data['EMA_50'] = data['close'].ewm(span=50, adjust=False).mean()

        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = data['close'].ewm(span=12, adjust=False).mean()
        exp2 = data['close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = exp1 - exp2
        data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['MACD_Histogram'] = data['MACD'] - data['Signal_Line']

        # Bollinger Bands
        data['BB_Middle'] = data['close'].rolling(window=20).mean()
        data['BB_Std'] = data['close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (data['BB_Std'] * 2)
        data['BB_Lower'] = data['BB_Middle'] - (data['BB_Std'] * 2)
        data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Middle']

        # Stochastic Oscillator
        low_14 = data['low'].rolling(window=14).min()
        high_14 = data['high'].rolling(window=14).max()
        data['%K'] = ((data['close'] - low_14) / (high_14 - low_14)) * 100
        data['%D'] = data['%K'].rolling(window=3).mean()

        # ATR (Average True Range)
        data['TR'] = np.maximum(
            data['high'] - data['low'],
            np.maximum(
                abs(data['high'] - data['close'].shift()),
                abs(data['low'] - data['close'].shift())
            )
        )
        data['ATR'] = data['TR'].rolling(window=14).mean()

        # ADX (Average Directional Index)
        plus_dm = np.maximum(data['high'] - data['high'].shift(), 0)
        minus_dm = np.maximum(data['low'].shift() - data['low'], 0)
        plus_dm[(plus_dm < minus_dm) | (plus_dm == minus_dm)] = 0
        minus_dm[(minus_dm < plus_dm) | (minus_dm == plus_dm)] = 0

        tr = data['TR']
        plus_di = 100 * (plus_dm.rolling(window=14).sum() / tr.rolling(window=14).sum())
        minus_di = 100 * (minus_dm.rolling(window=14).sum() / tr.rolling(window=14).sum())
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        data['ADX'] = dx.rolling(window=14).mean()

        # Momentum
        data['Momentum'] = data['close'] - data['close'].shift(4)

        # Rate of Change
        data['ROC'] = data['close'].pct_change(periods=12) * 100

        # On-Balance Volume (OBV)
        volume = data['real_volume'].where(data['real_volume'] != 0, data['tick_volume'])
        data['OBV'] = (np.sign(data['close'].diff()) * volume).cumsum()

        # Volume Rate of Change
        data['Volume_ROC'] = volume.pct_change(periods=1) * 100

        return data