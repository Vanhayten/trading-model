import MetaTrader5 as mt5
from trading_bot import TradingBot
from config import CONFIG
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_mt5():
    if not mt5.initialize():
        logger.error("MetaTrader5 initialization failed")
        return False

    if not mt5.login(CONFIG['MT5_LOGIN'], CONFIG['MT5_PASSWORD'], CONFIG['MT5_SERVER']):
        logger.error("MetaTrader5 login failed")
        mt5.shutdown()
        return False

    return True

if __name__ == "__main__":
    if initialize_mt5():
        trading_bot = TradingBot()

        # Run backtest
        #trading_bot.run_backtest()

        # Run live trading
        trading_bot.run()
    else:
        logger.error("Failed to initialize. Exiting.")