import MetaTrader5 as mt5
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_fetcher import DataFetcher
from trading_module import TradingModule, RiskManager
from llm_api_client import LLMApiClient
from backTester import BackTester
from config import CONFIG, Timeframe

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Set logging level to INFO for detailed logs

class TradingBot:
    def __init__(self):
        self.data_fetcher = DataFetcher(CONFIG['SYMBOL'], CONFIG['TIMEFRAME'])
        self.llm_api_client = LLMApiClient(CONFIG['LLM_API_URL'], CONFIG['LLM_API_KEY'])
        self.trading_module = TradingModule(self.llm_api_client)
        self.risk_manager = RiskManager()
        self.backtester = BackTester(self.data_fetcher, self.trading_module, self.risk_manager)

        if not mt5.initialize():
            logger.error("MetaTrader 5 initialization failed")
            raise RuntimeError("MetaTrader 5 initialization failed")

        logger.info("MetaTrader 5 initialized successfully")

    def run(self):
        while True:
            try:
                logger.info("Starting trading cycle")
                self._trading_cycle()
                logger.info(f"Sleeping for {CONFIG['TIMEFRAME'].value * 60} seconds until the next cycle")
                time.sleep(CONFIG['TIMEFRAME'].value * 60)  # Wait for the next candle
            except Exception as e:
                logger.error(f"An error occurred in the main loop: {e}")
                time.sleep(60)  # Wait for 1 minute before retrying


    def _trading_cycle(self):
        try:
            # Fetch the latest data (last 50 candles)
            latest_data = self.data_fetcher.fetch_latest_data(num_candles=50)

            # Fetch the current tick
            current_tick = self.data_fetcher.fetch_current_tick()

            # Combine the latest data with the current tick
            all_data = pd.concat([latest_data, current_tick.to_frame().T]).reset_index(drop=True)

            # Sort the data by time and reset the index
            all_data = all_data.sort_values('time').reset_index(drop=True)

            # Calculate indicators for the combined data
            decision_data = self.data_fetcher._add_technical_indicators(all_data)

            logger.info("Generating trading decisions")
            trading_decisions = self.trading_module.generate_trading_decisions(decision_data)

            self._display_real_time_decisions(trading_decisions)

            for decision in trading_decisions:
                self._execute_trade(decision)

        except Exception as e:
            logger.error(f"An error occurred in the trading cycle: {e}")


    def _display_real_time_decisions(self, decisions):
        print("\nReal-time Trading Decisions:")
        for i, decision in enumerate(decisions, 1):
            print(f"Decision {i}:")
            print(f"  Signal: {decision.signal}")
            print(f"  Stop Loss: {decision.stop_loss}")
            print(f"  Take Profit: {decision.take_profit}")
            print(f"  Explanation: {decision.explanation}")
            print()
            time.sleep(0.5)  # Simulate real-time display

    def _execute_trade(self, decision):
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Failed to get account info")
            return

        symbol_info = mt5.symbol_info(CONFIG['SYMBOL'])
        if symbol_info is None:
            logger.error(f"Failed to get symbol info for {CONFIG['SYMBOL']}")
            return

        point = symbol_info.point
        price = mt5.symbol_info_tick(CONFIG['SYMBOL']).ask if decision.signal == 'buy' else mt5.symbol_info_tick(CONFIG['SYMBOL']).bid

        stop_loss = self.risk_manager.adjust_stop_loss(price, decision.stop_loss, decision.take_profit)
        stop_loss_pips = abs(price - stop_loss) / point
        risk_amount = account_info.balance * CONFIG['MAX_RISK_PER_TRADE']
        position_size = self.risk_manager.calculate_position_size(account_info.balance, risk_amount, stop_loss_pips)

        # Ensure position size conforms to the symbol's lot requirements
        min_lot = symbol_info.volume_min
        max_lot = symbol_info.volume_max
        lot_step = symbol_info.volume_step

        if position_size < min_lot:
            position_size = min_lot
        elif position_size > max_lot:
            position_size = max_lot
        else:
            position_size = round(position_size / lot_step) * lot_step

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": CONFIG['SYMBOL'],
            "volume": position_size,
            "type": mt5.ORDER_TYPE_BUY if decision.signal == 'buy' else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": stop_loss,
            "tp": decision.take_profit,
            "deviation": 20,
            "magic": 234000,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed, retcode={result.retcode}")
        else:
            logger.info(f"Order executed: {result.order}")


    def run_backtest(self):
        start_date = datetime.strptime(CONFIG['BACKTESTING_START_DATE'], '%Y-%m-%d')
        end_date = datetime.strptime(CONFIG['BACKTESTING_END_DATE'], '%Y-%m-%d')
        results = self.backtester.run_backtest(start_date, end_date)
        self._analyze_backtest_results(results)

    def _analyze_backtest_results(self, results: pd.DataFrame):
        if results.empty:
            logger.warning("No backtest results to analyze.")
            return

        total_trades = len(results)
        winning_trades = results[results['pnl'] > 0]
        losing_trades = results[results['pnl'] <= 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        average_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        average_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if losing_trades['pnl'].sum() != 0 else float('inf')

        sharpe_ratio = self._calculate_sharpe_ratio(results['pnl'])
        max_drawdown = self._calculate_max_drawdown(results['balance'])

        logger.info(f"Backtest Results:")
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Win Rate: {win_rate:.2%}")
        logger.info(f"Average Win: ${average_win:.2f}")
        logger.info(f"Average Loss: ${average_loss:.2f}")
        logger.info(f"Profit Factor: {profit_factor:.2f}")
        logger.info(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        logger.info(f"Max Drawdown: {max_drawdown:.2%}")
        logger.info(f"Final Balance: ${results['balance'].iloc[-1]:.2f}")

    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02, periods: int = 252) -> float:
        excess_returns = returns - risk_free_rate / periods
        return np.sqrt(periods) * excess_returns.mean() / excess_returns.std() if excess_returns.std() != 0 else 0

    def _calculate_max_drawdown(self, balance: pd.Series) -> float:
        peak = balance.cummax()
        drawdown = (peak - balance) / peak
        return drawdown.max()
