import os
import time
from groq import Groq
from typing import Optional
from config.settings import settings

class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model_name = "llama3-70b-8192"
        self.max_retries = 3

    def generate_sql(self, messages: list) -> Optional[str]:
        """Generate SQL from messages with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model_name,
                    temperature=0.1,
                    max_tokens=512,
                )
                return self._extract_sql(response.choices[0].message.content)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return None

    def _extract_sql(self, response: str) -> Optional[str]:
        #print(response)
        """Extract SQL code from markdown block"""
        if '```sql' in response:
            return response.split('```sql')[1].split('```')[0].strip()
        if '```' in response:
            return response.split('```')[1].strip()
        return response