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
                validated_decision = self._validate_and_format_decision(trading_decision, one_minute_data)
                return [validated_decision] if validated_decision else []
            return []
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

    def _validate_and_format_decision(self, decision: dict, data: pd.DataFrame) -> TradingDecision:
        if not decision:
            return None

        current_price = data['close'].iloc[-1]

        if decision['signal'] not in ['buy', 'sell']:
            logger.warning(f"Invalid signal: {decision['signal']}")
            return None

        if decision['signal'] == 'buy' and not (decision['stop_loss'] < current_price < decision['take_profit']):
            logger.warning("Invalid buy decision: Stop Loss should be less than current price, and Take Profit should be greater")
            return None

        if decision['signal'] == 'sell' and not (decision['take_profit'] < current_price < decision['stop_loss']):
            logger.warning("Invalid sell decision: Take Profit should be less than current price, and Stop Loss should be greater")
            return None

        return TradingDecision(
            signal=decision['signal'],
            stop_loss=decision['stop_loss'],
            take_profit=decision['take_profit'],
            explanation=decision['explanation']
        )

    def _is_valid_decision(self, decision: dict, current_price: float) -> bool:
        return (
            decision["signal"] in ["buy", "sell"] and
            isinstance(decision["stop_loss"], float) and
            isinstance(decision["take_profit"], float) and
            decision["explanation"] and
            (decision["signal"] == "buy" and decision["stop_loss"] < current_price < decision["take_profit"] or
             decision["signal"] == "sell" and decision["take_profit"] < current_price < decision["stop_loss"])
        )