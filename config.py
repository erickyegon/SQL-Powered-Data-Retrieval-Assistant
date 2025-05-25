import os
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

# ===== GROQ MODEL OPTIONS =====
# Choose one of these models (uncomment the one you want to use):

# RECOMMENDED: Latest and most capable
MODEL_NAME = 'llama-3.3-70b-versatile'

# Alternative options (comment out the one above and uncomment one below):
# MODEL_NAME = 'llama-3.1-8b-instant'      # Faster, smaller model
# MODEL_NAME = 'llama3-70b-8192'           # Older but stable
# MODEL_NAME = 'llama3-8b-8192'            # Fastest, smallest
# MODEL_NAME = 'gemma2-9b-it'              # Google's model

# PREVIEW MODELS (experimental - may be discontinued):
# MODEL_NAME = 'deepseek-r1-distill-llama-70b'  # DeepSeek model
# MODEL_NAME = 'meta-llama/llama-4-scout-17b-16e-instruct'  # New Llama 4
# MODEL_NAME = 'meta-llama/llama-4-maverick-17b-128e-instruct'  # New Llama 4
# MODEL_NAME = 'qwen-qwq-32b'              # Alibaba's model

# Database configuration
DEFAULT_DB_HOST = os.getenv("DB_HOST", "localhost")
DEFAULT_DB_PORT = os.getenv("DB_PORT", "3306")
DEFAULT_DB_NAME = os.getenv("DB_NAME", "")
DEFAULT_DB_USER = os.getenv("DB_USER", "")
DEFAULT_DB_PASSWORD = os.getenv("DB_PASSWORD", "")
