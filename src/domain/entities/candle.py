from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float