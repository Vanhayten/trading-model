from typing import List
import pandas as pd
import logging
from domain.entities.trading_decision import TradingDecision
from infrastructure.external_services.llm_api_client import LLMApiClient

logger = logging.getLogger(__name__)

class TradingModule():
    def __init__(self, api_client: LLMApiClient):
        self.api_client = api_client

    def generate_trading_decisions(self, one_minute_data: pd.DataFrame, five_minute_data: pd.DataFrame) -> List[TradingDecision]:
        try:
            latest_one_minute_data = one_minute_data.tail(50).to_dict(orient='records')
            latest_five_minute_data = five_minute_data.tail(50).to_dict(orient='records')
            response = self.api_client.get_trading_decision(latest_one_minute_data, latest_five_minute_data)
            trading_decision = self._parse_llm_response(response)
            if trading_decision:
                validated_decision = self._validate_and_format_decision(trading_decision, one_minute_data, five_minute_data)
                if validated_decision:
                    return [validated_decision], True
                else:
                    return [], False
            return [], True
        except Exception as e:
            logger.error(f"Error occurred while generating trading decisions: {e}")
            return []

    def _parse_llm_response(self, response: str) -> dict:
        decision = {}
        lines = response.split('\n')
        for line in lines:
            if line.startswith("Signal:"):
                decision["signal"] = line.split(":")[1].strip()
            elif line.startswith("Stop Loss:"):
                try:
                    decision["stop_loss"] = float(line.split(":")[1].strip())
                except ValueError:
                    logger.error("Invalid Stop Loss value")
            elif line.startswith("Take Profit:"):
                try:
                    decision["take_profit"] = float(line.split(":")[1].strip())
                except ValueError:
                    logger.error("Invalid Take Profit value")
            elif line.startswith("Explanation:"):
                decision["explanation"] = line.split(":", 1)[1].strip()

        if "Insufficient data to make a trading decision" in response:
            logger.info("LLM reported insufficient data for a decision")
            return {}

        if all(key in decision for key in ["signal", "stop_loss", "take_profit", "explanation"]):
            return decision
        else:
            logger.error("Incomplete decision data received from LLM")
            return {}

    def _validate_and_format_decision(self, decision: dict, one_minute_data: pd.DataFrame, five_minute_data: pd.DataFrame) -> TradingDecision:
        current_price = one_minute_data['close'].iloc[-1]
        atr = one_minute_data['ATR'].iloc[-1]

        # Validate signal
        if decision['signal'] not in ['buy', 'sell']:
            logger.warning(f"Invalid signal: {decision['signal']}. Expected 'buy' or 'sell'.")
            return None

        # Validate stop loss and take profit
        if decision['signal'] == 'buy':
            if not (decision['stop_loss'] < current_price < decision['take_profit']):
                logger.warning(
                    f"Invalid stop loss or take profit for buy signal: Stop Loss = {decision['stop_loss']}, "
                    f"Current Price = {current_price}, Take Profit = {decision['take_profit']}"
                )
                return None
            if (current_price - decision['stop_loss']) < atr:
                logger.warning(
                    f"Stop loss too close to current price for buy signal: Stop Loss = {decision['stop_loss']}, "
                    f"Current Price = {current_price}, ATR = {atr}"
                )
                return None
        elif decision['signal'] == 'sell':
            if not (decision['take_profit'] < current_price < decision['stop_loss']):
                logger.warning(
                    f"Invalid stop loss or take profit for sell signal: Stop Loss = {decision['stop_loss']}, "
                    f"Current Price = {current_price}, Take Profit = {decision['take_profit']}"
                )
                return None
            if (decision['stop_loss'] - current_price) < atr:
                logger.warning(
                    f"Stop loss too close to current price for sell signal: Stop Loss = {decision['stop_loss']}, "
                    f"Current Price = {current_price}, ATR = {atr}"
                )
                return None

        # Check if decision aligns with overall trend
        if not self._check_trend_alignment(decision, one_minute_data, five_minute_data):
            logger.warning(
                f"Decision does not align with overall trend. Signal = {decision['signal']}, "
                f"Current Price = {current_price}, ATR = {atr}"
            )
            return None

        return TradingDecision(
            signal=decision['signal'],
            stop_loss=decision['stop_loss'],
            take_profit=decision['take_profit'],
            explanation=decision['explanation']
        )


    def _check_trend_alignment(self, decision: dict, one_minute_data: pd.DataFrame, five_minute_data: pd.DataFrame) -> bool:
        one_min_trend = self._determine_trend(one_minute_data)
        five_min_trend = self._determine_trend(five_minute_data)

        if decision['signal'] == 'buy':
            return one_min_trend == 'up' and five_min_trend in ['up', 'neutral']
        elif decision['signal'] == 'sell':
            return one_min_trend == 'down' and five_min_trend in ['down', 'neutral']

    def _determine_trend(self, data: pd.DataFrame) -> str:
        sma_short = data['SMA_20'].iloc[-1]
        sma_long = data['SMA_20'].rolling(window=20).mean().iloc[-1]

        if sma_short > sma_long and data['ADX'].iloc[-1] > 25:
            return 'up'
        elif sma_short < sma_long and data['ADX'].iloc[-1] > 25:
            return 'down'
        else:
            return 'neutral'

    def _is_valid_decision(self, decision: dict, current_price: float) -> bool:
        return (
            decision["signal"] in ["buy", "sell"] and
            isinstance(decision["stop_loss"], float) and
            isinstance(decision["take_profit"], float) and
            decision["explanation"] and
            (decision["signal"] == "buy" and decision["stop_loss"] < current_price < decision["take_profit"] or
             decision["signal"] == "sell" and decision["take_profit"] < current_price < decision["stop_loss"])
        )
