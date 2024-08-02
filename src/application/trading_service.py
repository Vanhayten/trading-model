import MetaTrader5 as mt5
import sys
import time
import datetime
import logging
from infrastructure.data_providers.mt5_data_provider import DataFetcher
from infrastructure.trading_strategies.llm_trading_strategy import TradingModule
from infrastructure.risk_managers.basic_risk_manager import RiskManager
from infrastructure.external_services.llm_api_client import LLMApiClient
from config.settings import CONFIG
from domain.value_objects.timeframe import Timeframe

logger = logging.getLogger(__name__)

class TradingService:
    def __init__(self):
        self.data_fetcher = DataFetcher(CONFIG['SYMBOL'])
        llm_api_client = LLMApiClient(CONFIG['LLM_API_URL'], CONFIG['LLM_API_KEY'])
        self.trading_module = TradingModule(llm_api_client)
        self.risk_manager = RiskManager()
        self.cooldown_period = CONFIG['CYCLE_INTERVAL'] * 60
        self.last_trade_time = None

    def run(self):
        while True:
            try:
                self._trading_cycle()
                logger.info(f"Sleeping for {self.cooldown_period} seconds until the next cycle")
                self._start_countdown(CONFIG['CYCLE_INTERVAL'] * 60)
            except Exception as e:
                logger.error(f"An error occurred in the main loop: {e}")
                time.sleep(60)

    def _start_countdown(self, duration):
        start_time = time.time()
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            remaining = max(0, duration - elapsed)
            minutes, seconds = divmod(int(remaining), 60)
            sys.stdout.write(f"\rCooldown: {minutes:02}:{seconds:02}")
            sys.stdout.flush()
            time.sleep(1)  # Update every second
        sys.stdout.write("\rCooldown: 00:00\n")
        sys.stdout.flush()


    def _trading_cycle(self):
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                self.data_fetcher.ensure_mt5_connection()

                account_info = mt5.account_info()
                if account_info is None:
                    logger.error(f"Failed to get account info : {mt5.last_error()}")
                    return

                open_positions = mt5.positions_get(symbol=CONFIG['SYMBOL'])
                if open_positions is None:
                    logger.error(f"Failed to get open positions for {CONFIG['SYMBOL']}  error : {mt5.last_error()}")
                    return

                # Fetch the latest 1-minute and 5-minute data (last 50 candles each)
                latest_1m_data = self.data_fetcher.fetch_latest_data(timeframe=Timeframe["M1"], num_candles=50, extra_candles = 100)
                latest_5m_data = self.data_fetcher.fetch_latest_data(timeframe=Timeframe["M5"], num_candles=50, extra_candles = 100)

                # Sort the data by time and reset the index
                latest_1m_data = latest_1m_data.sort_values('time').reset_index(drop=True)
                latest_5m_data = latest_5m_data.sort_values('time').reset_index(drop=True)

                market_data = {
                        '1m': latest_1m_data,
                        '5m': latest_5m_data
                    }

                if not self.risk_manager.can_open_more_trades(account_info, open_positions, market_data):
                    logger.warning("Skipping trading cycle due to risk management constraints")
                    return

                logger.info("Generating trading decisions")
                trading_decisions, is_valid = self.trading_module.generate_trading_decisions(latest_1m_data, latest_5m_data)

                if is_valid:
                    for decision in trading_decisions:
                        if self.risk_manager.should_execute_trade(decision, open_positions):
                            self._display_real_time_decisions(trading_decisions)
                            self._execute_trade(decision)
                    return
                else:
                    logger.warning(f"Invalid trading decision on attempt {attempt + 1}. Retrying immediately...")
                    attempt += 1

            except Exception as e:
                logger.error(f"An error occurred in the trading cycle: {e}")

        logger.warning(f"Max attempts ({max_attempts}) reached. Unable to generate valid trading decisions.")

    def _display_real_time_decisions(self, decisions):
        print("\nReal-time Trading Decisions:")
        for i, decision in enumerate(decisions, 1):
            print(f"Decision {i}:")
            print(f"  Signal: {decision.signal}")
            print(f"  Stop Loss: {decision.stop_loss}")
            print(f"  Take Profit: {decision.take_profit}")
            print(f"  Explanation: {decision.explanation}")
            print()

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
            logger.error(f"Order failed, retcode={result.retcode} message : {result.comment}")
        else:
            logger.info(f"Order executed: {result.order}")

