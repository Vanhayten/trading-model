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
            Analyze the following XAUUSD data:

            1-minute chart data (last 50 candles):
            {one_minute_data}

            5-minute chart data (last 50 candles):
            {five_minute_data}

            Each candle includes: Timestamp, Open, High, Low, Close, Volume, SMA, EMA, RSI, MACD, Bollinger Bands

            Based on this comprehensive data, generate ONE precise trading decision. Your response MUST EXACTLY follow this format:

            Signal: [ONLY 'buy' or 'sell']
            Stop Loss: [EXACT price number]
            Take Profit: [EXACT price number]
            Explanation: [1-2 sentences ONLY]

            CRITICAL RULES:
            1. Adhere STRICTLY to the format above. No additional text allowed.
            2. Signal MUST be either 'buy' or 'sell'. No alternatives permitted.
            3. Stop Loss and Take Profit MUST be specific numerical values.
            4. For 'buy': Stop Loss < current price < Take Profit
            5. For 'sell': Take Profit < current price < Stop Loss
            6. Explanation MUST be concise (1-2 sentences max) focusing ONLY on the primary reason for the decision.
            7. DO NOT include any analysis, questions, or extra commentary.
            8. If data is insufficient, respond ONLY with: "Insufficient data to make a trading decision."

            IMPORTANT:
            - Analyze both 1-minute and 5-minute timeframes for a comprehensive view.
            - Consider recent price action, trends, and potential reversals.
            - Pay attention to key technical indicators and their crossovers.
            - Look for significant support/resistance levels in both timeframes.
            - Ensure your decision aligns with the overall trend visible in the data.

            Your adherence to these guidelines is crucial. Any deviation will be considered an error and may result in incorrect trading decisions.
            """
        return prompt