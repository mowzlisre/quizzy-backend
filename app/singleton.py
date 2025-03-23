# singleton.py
import nltk

_downloaded = set()

def safe_nltk_download(resource, path=None):
    if resource in _downloaded:
        return  # Already handled in this session

    try:
        nltk.data.find(path if path else resource)
    except LookupError:
        nltk.download(resource)
    _downloaded.add(resource)
