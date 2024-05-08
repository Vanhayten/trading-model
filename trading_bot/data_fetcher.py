from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd

class DataFetcher:
    def __init__(self, symbol, timeframe):
        self.symbol = symbol
        self.timeframe = timeframe

    def fetch_historical_data(self, num_data_points=500):
        date_from, date_to = self.calculate_date_range()
        rates = self.get_rates(date_from, date_to)
        data = self.preprocess_data(rates, num_data_points)
        return data

    def calculate_date_range(self):
        date_from = datetime.now() - timedelta(days=2)
        date_to = datetime.now()
        return date_from, date_to

    def get_rates(self, date_from, date_to):
        rates = pd.DataFrame(mt5.copy_rates_range(self.symbol, self.timeframe, date_from, date_to))
        rates["time"] = pd.to_datetime(rates["time"], unit="s")
        print(rates)
        return rates

    def preprocess_data(self, rates, num_data_points):
        return rates.tail(num_data_points)