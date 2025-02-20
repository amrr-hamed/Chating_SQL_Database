import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from config.settings import settings
from typing import List, Dict

class SchemaRetriever:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.embedding_dim = self.model.encode(["test"]).shape[1]  # Dynamically determine embedding size
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.schemas: List[Dict] = []  # Store schema metadata dictionaries
        self._load_existing_index()

    def _load_existing_index(self):
        """Load existing FAISS index and schema mapping if available"""
        try:
            self.index = faiss.read_index(str(settings.FAISS_INDEX))
            with open(settings.SCHEMA_MAPPING, "r") as f:
                self.schemas = json.load(f)
        except (FileNotFoundError, RuntimeError):
            # Initialize empty index if no existing index is found
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.schemas = []

    def update_index(self, schema_data: Dict[str, str], db_id: str):
        """Update index with new schemas from a database"""
        schema_texts = list(schema_data.values())  # Convert schema data to list of texts for embedding
        embeddings = self.model.encode(schema_texts, normalize_embeddings=True).astype('float32')

        # Update FAISS index
        self.index.add(embeddings)

        # Store metadata with database reference
        for (table, text), embedding in zip(schema_data.items(), embeddings):
            self.schemas.append({
                "db_id": db_id,
                "table": table,
                "schema_text": text,
                "embedding": embedding.tolist()  # Store corresponding embedding
            })

        # Persist to disk
        self._save_index()

    def _save_index(self):
        """Save index and metadata to disk"""
        faiss.write_index(self.index, str(settings.FAISS_INDEX))
        with open(settings.SCHEMA_MAPPING, "w") as f:
            json.dump(self.schemas, f)

    def retrieve(self, question: str, k: int = 3) -> List[Dict]:
        """Retrieve top-k relevant schemas with metadata"""
        question_embed = self.model.encode([question], normalize_embeddings=True).astype('float32')
        _, indices = self.index.search(np.array(question_embed), k)

        valid_indices = [i for i in indices[0] if 0 <= i < len(self.schemas)]
        retrieved_schemas = [self.schemas[i] for i in valid_indices[:k]]

        # Extract only the schema text for PromptEngineer
        schema_texts = [schema["schema_text"] for schema in retrieved_schemas]

        return schema_texts  # Return list of schema strings