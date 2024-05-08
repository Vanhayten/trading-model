import ollama
import json

class TradingModule:
    def __init__(self, prompt_template):
        self.prompt_template = prompt_template

    def generate_trading_decisions(self, candlestick_data):
        prompt = self.prompt_template.format(data=candlestick_data)
        query = f'{prompt}'
        try:
            response = ollama.chat(model='phi3', messages=[{'role': 'user', 'content': query}])
            trading_decisions = response['message']['content'].strip().split("\n\n")
            print(trading_decisions)
            return self.validate_and_format_decisions(trading_decisions)
        except Exception as e:
            print(f"Error occurred while generating trading decisions: {e}")
            return []

    def validate_and_format_decisions(self, trading_decisions):
        validated_decisions = []
        for decision in trading_decisions:

            lines = decision.split("\n")

            signal = lines[0].strip()
            stop_loss = lines[1].split(": ")[1].strip()
            take_profit = lines[2].split(": ")[1].strip()
            explanation = "\n".join(lines[3:])


            trading_decision_json = {
                "signal": signal,
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "explanation": explanation
            }

            validated_decisions.append(trading_decision_json)

        return validated_decisions

    def execute_trade(self, trading_decision):
        signal = trading_decision["signal"]
        stop_loss = trading_decision["stop_loss"]
        take_profit = trading_decision["take_profit"]
        explanation = trading_decision["explanation"]

        # Implement your trading logic here
        # Place trades based on the signal, stop_loss, and take-profit levels

        print(f"Trading Decision: Signal={signal}, Stop Loss={stop_loss}, Take Profit={take_profit}")
        print(f"Explanation: {explanation}")