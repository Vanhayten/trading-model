from config.settings import CONFIG

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