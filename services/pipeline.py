from typing import Tuple, Optional
from pathlib import Path
from .schema_retriever import SchemaRetriever
from .prompt_engineer import PromptEngineer
from .llm_client import GroqClient
from .query_executor import QueryExecutor
from config.settings import settings

class TextToSQLPipeline:
    def __init__(self):
        self.retriever = SchemaRetriever()
        self.llm_client = GroqClient()
    
    def process_query(self, question: str, db_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """Full processing pipeline"""
        try:
            # Retrieve relevant schemas
            schemas = self.retriever.retrieve(question)
            if not schemas:
                return None, "No relevant schemas found"

            # Generate SQL
            prompt = PromptEngineer.build_prompt(question, schemas)
            sql = self.llm_client.generate_sql(prompt)
            if not sql:
                return None, "Failed to generate SQL"

            # Execute query
            executor = QueryExecutor(db_path)
            results, error = executor.execute_safe_query(sql)
            return results, error

        except Exception as e:
            return None, f"Pipeline Error: {str(e)}"