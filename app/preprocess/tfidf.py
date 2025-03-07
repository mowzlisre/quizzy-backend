import fitz  # PyMuPDF for PDF text extraction
import nltk
import spacy
import string
from sklearn.feature_extraction.text import TfidfVectorizer

# 📝 Load NLP Models
nltk.download("punkt")
nltk.download("stopwords")
nlp = spacy.load("en_core_web_sm")

# 📝 Function to Extract Text from a PDF File
def extract_text_from_pdf(pdf_path):
    """Extracts raw text from a given PDF file using PyMuPDF."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

# 📝 Function to Preprocess Text (Tokenization, Stopword Removal)
def preprocess_text(text):
    """Tokenizes text, removes stopwords and punctuation, and returns cleaned words."""
    stop_words = set(nltk.corpus.stopwords.words("english"))
    words = nltk.word_tokenize(text.lower())
    words = [word for word in words if word not in stop_words and word not in string.punctuation]
    return " ".join(words)

# 📝 Function to Extract Coherent Words Using TF-IDF
def extract_coherent_words(text, top_n=15):
    """Uses TF-IDF to extract the most statistically significant words with their scores."""
    vectorizer = TfidfVectorizer(stop_words="english", max_features=top_n)
    tfidf_matrix = vectorizer.fit_transform([text])
    words = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]  # Extract scores for words

    # Convert to a list of tuples (word, score)
    word_scores = list(zip(words, scores))

    # Sort by coherence score in descending order
    return sorted(word_scores, key=lambda x: x[1], reverse=True)

# 📝 Function to Extract the Most Coherent Words and Phrases with Scores
def get_coherent_terms_from_pdf(pdf_path):
    """Extracts the most relevant words from a given PDF file, along with their coherence values."""
    extracted_text = extract_text_from_pdf(pdf_path)
    cleaned_text = preprocess_text(extracted_text)

    # Extract words and phrases with scores
    coherent_words = extract_coherent_words(cleaned_text, top_n=15)

    return coherent_words  # List of (word, score) tuples

# 📝 Function to Perform TF-IDF and Return Native Python Data Structure
def performTFIDF(path):
    return get_coherent_terms_from_pdf(path)
