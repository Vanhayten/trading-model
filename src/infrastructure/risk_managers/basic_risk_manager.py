import MetaTrader5 as mt5
from config.settings import CONFIG
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RiskManager():
    def __init__(self, max_risk_per_trade: float = CONFIG['MAX_RISK_PER_TRADE']):
        self.max_risk_per_trade = max_risk_per_trade

    def calculate_position_size(self, account_balance: float, risk_amount: float, stop_loss_pips: float) -> float:
        max_risk_amount = account_balance * self.max_risk_per_trade
        risk_amount = min(risk_amount, max_risk_amount)
        position_size = risk_amount / stop_loss_pips
        return round(position_size, 4)

    def adjust_stop_loss(self, entry_price: float, stop_loss: float, take_profit: float) -> float:
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        if reward / risk < 2:
            return entry_price - (take_profit - entry_price) / 2
        return stop_loss

    def should_execute_trade(self, decision, open_positions):
        for position in open_positions:
            if (position.type == mt5.POSITION_TYPE_BUY and decision.signal == 'buy') or \
               (position.type == mt5.POSITION_TYPE_SELL and decision.signal == 'sell'):
                logger.info("Skipping trade due to existing position in same direction")
                return False
        return True

    def can_open_more_trades(self, account_info, open_positions, market_data):

        # 1. Check account health
        equity = account_info.equity
        balance = account_info.balance
        margin_level = (equity / account_info.margin) * 100 if account_info.margin > 0 else float('inf')

        if margin_level < CONFIG['MIN_MARGIN_LEVEL']:  # Conservative margin level threshold
            logger.error(f"Margin level ({margin_level:.2f}%) below minimum ({CONFIG['MIN_MARGIN_LEVEL']}%)")
            return False

        # 2. Check open positions
        num_open_positions = len(open_positions)
        if num_open_positions >= CONFIG['MAX_SIMULTANEOUS_POSITIONS']:
            logger.error(f"Maximum simultaneous positions ({CONFIG['MAX_SIMULTANEOUS_POSITIONS']}) reached")
            return False

        # 3. Calculate current drawdown
        drawdown = (balance - equity) / balance
        if drawdown > CONFIG['MAX_DRAWDOWN']:
            return False

        volatility_thresholds = {
            '1m': CONFIG['1MIN_MAX_VOLATILITY'],  # 0.5% for 1-minute timeframe
            '5m': CONFIG['5MIN_MAX_VOLATILITY'],  # 0.3% for 5-minute timeframe
        }

        for timeframe, data in market_data.items():
            if timeframe not in volatility_thresholds:
                logger.error(f"Unsupported timeframe: {timeframe}")
                continue

            recent_prices = data['close'].tail(20)  # Last 20 periods
            volatility = np.std(recent_prices.pct_change())
            if volatility > volatility_thresholds[timeframe]:
                logger.info(f"Volatility for timeframe {timeframe} ({volatility:.2f}) exceeds maximum ({volatility_thresholds[timeframe]})")
                return False

        # 5. Time-based rules
        current_hour = datetime.now().hour
        if current_hour in CONFIG['NO_TRADE_HOURS']:
            logger.error(f"Trading is not allowed during hour {current_hour} as per NO_TRADE_HOURS configuration.")
            return False

        return True