import requests
import logging
from typing import List, Dict
from config.settings import CONFIG
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMApiClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def get_trading_decision(self, one_minute_data: List[Dict], five_minute_data: List[Dict]) -> str:
        prompt = self._generate_prompt(one_minute_data, five_minute_data)
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise

    def _generate_prompt(self, one_minute_data: List[Dict], five_minute_data: List[Dict]) -> str:
        prompt = f"""
        Analyze the {CONFIG['SYMBOL']} data provided for 1-minute and 5-minute timeframes.

        1-minute chart data (last 50 candles):
        {one_minute_data}

        5-minute chart data (last 50 candles):
        {five_minute_data}

        Based on this data, provide ONE precise trading decision following these rules:

        1. Signal must be either 'buy' or 'sell'.
        2. Stop Loss and Take Profit must be specific numerical values.
        3. For 'buy': Stop Loss < current price < Take Profit
        4. For 'sell': Take Profit < current price < Stop Loss
        5. Stop Loss should be at least 1 ATR away from the current price.
        6. The decision should align with the overall trend visible in both timeframes.
        7. Consider recent price action, key technical indicators, and significant support/resistance levels.

        Provide your decision in this exact format:

        Signal: [buy/sell]
        Stop Loss: [exact price]
        Take Profit: [exact price]
        Explanation: [1-2 sentences explaining the primary reason for the decision]

        If the data is insufficient or unclear, respond only with: "Insufficient data to make a trading decision."

        Your strict adherence to these guidelines is crucial for accurate trading decisions.
        """
        return prompt