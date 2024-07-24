from dataclasses import dataclass

@dataclass
class TradingDecision:
    signal: str
    stop_loss: float
    take_profit: float
    explanation: str