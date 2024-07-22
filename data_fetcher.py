import MetaTrader5 as mt5
import pandas as pd
import time
import logging
from datetime import datetime
from config import CONFIG, Timeframe

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, symbol: str, timeframe: Timeframe):
        self.symbol = symbol
        self.timeframe = timeframe.value

    def ensure_mt5_connection(self):
        if not mt5.initialize():
            logger.error("MetaTrader5 initialization failed")
            raise Exception("MetaTrader5 initialization failed")

        if not mt5.login(CONFIG['MT5_LOGIN'], CONFIG['MT5_PASSWORD'], CONFIG['MT5_SERVER']):
            logger.error("MetaTrader5 login failed")
            mt5.shutdown()
            raise Exception("MetaTrader5 login failed")

    def fetch_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
            self.ensure_mt5_connection()
            all_data = pd.DataFrame()

            chunk_size = pd.DateOffset(weeks=1)
            current_start_date = start_date

            while current_start_date < end_date:
                current_end_date = min(current_start_date + chunk_size, end_date)
                for attempt in range(CONFIG['MAX_RETRIES']):
                    try:
                        rates = pd.DataFrame(mt5.copy_rates_range(self.symbol, self.timeframe, current_start_date, current_end_date))
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

    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        # SMA and EMA
        data['SMA_20'] = data['close'].rolling(window=20, min_periods=1).mean()
        data['EMA_50'] = data['close'].ewm(span=50, adjust=False, min_periods=1).mean()

        # RSI
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14, min_periods=1).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = data['close'].ewm(span=12, adjust=False, min_periods=1).mean()
        exp2 = data['close'].ewm(span=26, adjust=False, min_periods=1).mean()
        data['MACD'] = exp1 - exp2
        data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False, min_periods=1).mean()

        # Bollinger Bands
        data['BB_Middle'] = data['close'].rolling(window=20, min_periods=1).mean()
        data['BB_Upper'] = data['BB_Middle'] + (data['close'].rolling(window=20, min_periods=1).std() * 2)
        data['BB_Lower'] = data['BB_Middle'] - (data['close'].rolling(window=20, min_periods=1).std() * 2)

        # Stochastic Oscillator
        low_14 = data['low'].rolling(window=14, min_periods=1).min()
        high_14 = data['high'].rolling(window=14, min_periods=1).max()
        data['%K'] = (data['close'] - low_14) * 100 / (high_14 - low_14)
        data['%D'] = data['%K'].rolling(window=3, min_periods=1).mean()

        # Fill NaN values
        data = data.fillna(method='bfill')  # Backfill
        data = data.fillna(method='ffill')  # Forward fill any remaining NaNs

        return data


    def fetch_latest_data(self, num_candles: int = 50) -> pd.DataFrame:
        self.ensure_mt5_connection()

        for attempt in range(CONFIG['MAX_RETRIES']):
            try:
                # Fetch the most recent completed candles
                rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, num_candles)
                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')

                    print(f"Fetched data from {df['time'].min()} to {df['time'].max()}")
                    print(f"Current time: {datetime.now()}")
                    print(f"MetaTrader server time: {mt5.symbol_info(self.symbol).time}")

                    return self._add_technical_indicators(df)
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