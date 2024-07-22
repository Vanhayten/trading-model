import pandas as pd
import numpy as np
from typing import List, Tuple
from datetime import datetime, timedelta
from data_fetcher import DataFetcher
from trading_module import TradingModule, RiskManager, TradingDecision
from config import CONFIG, Timeframe

class BackTester:
    def __init__(self, data_fetcher: DataFetcher, trading_module: TradingModule, risk_manager: RiskManager):
        self.data_fetcher = data_fetcher
        self.trading_module = trading_module
        self.risk_manager = risk_manager
        self.initial_balance = 200  # Starting balance for backtesting

    def run_backtest(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        data = self.data_fetcher.fetch_historical_data(start_date, end_date)
        trades = []
        balance = self.initial_balance

        for i in range(len(data) - 50):  # Use a 50-candle lookback window
            window = data.iloc[i:i+50]
            decisions = self.trading_module.generate_trading_decisions(window)

            for decision in decisions:
                entry_price = window['close'].iloc[-1]
                stop_loss = self.risk_manager.adjust_stop_loss(entry_price, decision.stop_loss, decision.take_profit)
                risk_amount = balance * CONFIG['MAX_RISK_PER_TRADE']
                position_size = self.risk_manager.calculate_position_size(balance, risk_amount, abs(entry_price - stop_loss))

                exit_price, exit_time = self._simulate_trade(data.iloc[i+50:], decision, entry_price, stop_loss, decision.take_profit)

                pnl = (exit_price - entry_price) * position_size if decision.signal == 'buy' else (entry_price - exit_price) * position_size
                balance += pnl

                trades.append({
                    'entry_time': window.index[-1],
                    'exit_time': exit_time,
                    'signal': decision.signal,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'stop_loss': stop_loss,
                    'take_profit': decision.take_profit,
                    'position_size': position_size,
                    'pnl': pnl,
                    'balance': balance
                })

        return pd.DataFrame(trades)

    def _simulate_trade(self, future_data: pd.DataFrame, decision: TradingDecision, entry_price: float, stop_loss: float, take_profit: float) -> Tuple[float, pd.Timestamp]:
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