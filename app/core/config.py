# core/config.py

import os
from dotenv import load_dotenv

load_dotenv()
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "openai").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

VECTOR_DIM = int(os.getenv("VECTOR_DIM", "1536"))

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")
