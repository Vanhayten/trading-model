import requests
import logging
from typing import List, Dict, Generator
from config import CONFIG
from openai import OpenAI


logger = logging.getLogger(__name__)

class LLMApiClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def get_trading_decision(self, data: List[Dict]) -> str:
        prompt = self._generate_prompt(data)
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

    def _generate_prompt(self, data: List[Dict]) -> str:
        prompt = f"""
        Analyze the following XAUUSD 5-minute candlestick data:

        {data}

        Based on this data, generate ONE trading decision. Your response MUST EXACTLY follow this format, with no deviations or additional text:

        Signal: [ONLY 'buy' or 'sell']
        Stop Loss: [EXACT price number]
        Take Profit: [EXACT price number]
        Explanation: [1-2 sentences ONLY]

        CRITICAL RULES:
        1. Use ONLY the format above. Do not add any other text.
        2. Signal MUST be either 'buy' or 'sell'. No other words allowed.
        3. Stop Loss and Take Profit MUST be specific numerical values.
        4. For 'buy': Stop Loss < current price < Take Profit
        5. For 'sell': Take Profit < current price < Stop Loss
        6. Explanation MUST be brief (1-2 sentences max) and ONLY about the main reason for the decision.
        7. DO NOT include any analysis, questions, or additional commentary.
        8. If you cannot make a decision, respond ONLY with: "Insufficient data to make a trading decision."

        REMEMBER: Strict adherence to this format is REQUIRED. Any deviation will be considered an error.
        """
        return prompt