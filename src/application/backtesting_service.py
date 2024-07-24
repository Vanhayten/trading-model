import pandas as pd
import numpy as np
from datetime import datetime
from infrastructure.data_providers.mt5_data_provider import DataFetcher
from infrastructure.trading_strategies.llm_trading_strategy import TradingModule
from infrastructure.risk_managers.basic_risk_manager import RiskManager
from infrastructure.external_services.llm_api_client import LLMApiClient
from config.settings import CONFIG
import logging

logger = logging.getLogger(__name__)

class BacktestingService:
    def __init__(self):
        self.data_fetcher = DataFetcher(CONFIG['SYMBOL'], CONFIG['TIMEFRAME'])
        llm_api_client = LLMApiClient(CONFIG['LLM_API_URL'], CONFIG['LLM_API_KEY'])
        self.trading_module = TradingModule(llm_api_client)
        self.risk_manager = RiskManager()
        self.initial_balance = 200

    def run_backtest(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        start_date = datetime.strptime(CONFIG['BACKTESTING_START_DATE'], '%Y-%m-%d')
        end_date = datetime.strptime(CONFIG['BACKTESTING_END_DATE'], '%Y-%m-%d')
        results = self.backtester.run_backtest(start_date, end_date)
        self._analyze_backtest_results(results)

    def _simulate_trade(self, future_data: pd.DataFrame, decision, entry_price: float, stop_loss: float, take_profit: float):
        for _, candle in future_data.iterrows():
            if decision.signal == 'buy':
                if candle['low'] <= stop_loss:
                    return stop_loss, candle.name
                elif candle['high'] >= take_profit:
                    return take_profit, candle.name
            else:  # sell
                if candle['high'] >= stop_loss:
                    return stop_loss, candle.name
                elif candle['low'] <= take_profit:
                    return take_profit, candle.name

        # If the trade hasn't been closed, close at the last available price
        return future_data['close'].iloc[-1], future_data.index[-1]

    def analyze_results(self, results: pd.DataFrame):
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