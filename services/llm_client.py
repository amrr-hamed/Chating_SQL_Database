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

import re
from typing import Optional

class SQLExtractor:
    
    @staticmethod
    def _is_safe_sql(query: str) -> bool:
        """Check if the extracted SQL query is safe."""
        dangerous_patterns = [
            r"\bDROP\b", r"\bDELETE\b", r"\bALTER\b", r"\bTRUNCATE\b", r";--", r"' OR '1'='1'",
            r"--", r"UNION.*SELECT", r"INSERT INTO", r"UPDATE .* SET"
        ]
        return not any(re.search(pattern, query, re.IGNORECASE) for pattern in dangerous_patterns)

    def _extract_sql(self, response: str) -> Optional[str]:
        """Extract and validate SQL code from markdown block"""
        if '```sql' in response:
            query = response.split('```sql')[1].split('```')[0].strip()
        elif '```' in response:
            query = response.split('```')[1].strip()
        else:
            return response  # No SQL block found
        
        # 🚨 **Security Check Before Returning Query**
        if not self._is_safe_sql(query):
            print("⚠️ WARNING: Potentially unsafe SQL detected! Query rejected.")
            return None  # Reject unsafe queries
        
        return query
