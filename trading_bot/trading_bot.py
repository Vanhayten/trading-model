from data_fetcher import DataFetcher
from trading_module import TradingModule
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBot:
    def __init__(self, symbol, timeframe, prompt_template):
        self.symbol = symbol
        self.timeframe = timeframe
        self.prompt_template = prompt_template

    def run(self):
        data_fetcher = DataFetcher(self.symbol, self.timeframe)
        trading_module = TradingModule(self.prompt_template)

        while True:
            latest_data = data_fetcher.fetch_historical_data()
            trading_decisions = trading_module.generate_trading_decisions(latest_data.to_string(index=False))

            for decision in trading_decisions:
                trading_module.execute_trade(decision)

            time.sleep(300)  # Wait for 5 minutes before fetching new data