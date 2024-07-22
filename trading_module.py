from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging
import numpy as np
import pandas as pd
from config import CONFIG
from typing import List, Dict, Generator

logger = logging.getLogger(__name__)

@dataclass
class TradingDecision:
    signal: str
    stop_loss: float
    take_profit: float
    explanation: str

class TradingModule:
    def __init__(self, api_client):
        self.api_client = api_client

    def generate_trading_decisions(self, data: pd.DataFrame) -> List[TradingDecision]:
        try:
            latest_data = data.tail(50).to_dict(orient='records')
            response = self.api_client.get_trading_decision(latest_data)
            trading_decision = self._parse_llm_response(response)
            if trading_decision:
                validated_decision = self._validate_and_format_decision(trading_decision, data)
                return [validated_decision] if validated_decision else []
            return []
        except Exception as e:
            logger.error(f"Error occurred while generating trading decisions: {e}")
            return []

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
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

    def _validate_and_format_decision(self, decision: Dict[str, Any], data: pd.DataFrame) -> Optional[TradingDecision]:
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

    def _is_valid_decision(self, decision: Dict[str, Any], current_price: float) -> bool:
        return (
            decision["signal"] in ["buy", "sell"] and
            isinstance(decision["stop_loss"], float) and
            isinstance(decision["take_profit"], float) and
            decision["explanation"] and
            (decision["signal"] == "buy" and decision["stop_loss"] < current_price < decision["take_profit"] or
             decision["signal"] == "sell" and decision["take_profit"] < current_price < decision["stop_loss"])
        )

class RiskManager:
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