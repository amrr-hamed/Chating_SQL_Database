from typing import List

class PromptEngineer:
    SYSTEM_PROMPT = """You are a SQL expert assistant. Generate safe, efficient SQL queries based on the database schema and user questions.

Relevant Schema:
{schemas}

Rules:
1. Use explicit JOIN syntax
2. Always include LIMIT clause
3. Avoid SELECT *
4. Use ISO date formats
5. Never modify data"""

    @classmethod
    def build_prompt(cls, question: str, schemas: List[str]) -> list:
        print(schemas)
        return [
            {"role": "system", "content": cls.SYSTEM_PROMPT.format(schemas="\n\n".join(schemas))},
            {"role": "user", "content": f"Question: {question}\nSQL:"}
        ]