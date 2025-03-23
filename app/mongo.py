from pymongo import MongoClient
from django.conf import settings
import re
from nltk.tokenize import sent_tokenize
from .singleton import safe_nltk_download

safe_nltk_download("punkt_tab", "tokenizers/punkt_tab")

mongo_client = MongoClient(settings.MONGO_DB_CLIENT)
mongo_db = mongo_client[settings.MONGO_DB_NAME]
mongo_collection = mongo_db["file_chunks"]


def preprocess_text(text):
    """Cleans text before chunking."""
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    text = re.sub(r'\n+', ' ', text)  # Remove excessive new lines
    return text

def chunk_text(text, chunk_size=500):
    """Splits text into structured chunks."""
    text = preprocess_text(text)
    sentences = sent_tokenize(text)  # Split text into sentences
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())  # Store the finalized chunk
            current_chunk = sentence  # Start new chunk

    if current_chunk:
        chunks.append(current_chunk.strip())  # Add last chunk
    print(len(chunks))
    return chunks, text