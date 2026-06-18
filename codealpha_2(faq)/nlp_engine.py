import json
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize NLTK resources
def setup_nltk():
    for res in ['punkt', 'stopwords', 'wordnet']:
        try:
            nltk.download(res, quiet=True)
        except Exception as e:
            print(f"Warning: could not download NLTK resource {res}: {e}")

setup_nltk()

class FAQBot:
    def __init__(self, faq_file_path):
        with open(faq_file_path, 'r', encoding='utf-8') as f:
            self.faqs = json.load(f)
        
        self.lemmatizer = WordNetLemmatizer()
        
        # Retrieve English stopwords
        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception:
            # Fallback in case stopwords corpus is not loaded correctly
            self.stop_words = {"i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
                               "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", 
                               "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", 
                               "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", 
                               "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", 
                               "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", 
                               "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", 
                               "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", 
                               "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", 
                               "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", 
                               "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
                               "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"}
        
        # Preprocess all FAQ questions
        self.preprocessed_questions = [self.preprocess(faq['question']) for faq in self.faqs]
        
        # Initialize and fit TF-IDF Vectorizer
        self.vectorizer = TfidfVectorizer()
        if self.preprocessed_questions:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.preprocessed_questions)
        else:
            self.tfidf_matrix = None

    def preprocess(self, text):
        # 1. Lowercase
        text = text.lower()
        # 2. Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # 3. Tokenize
        try:
            tokens = word_tokenize(text)
        except Exception:
            # Fallback space tokenizer if nltk.word_tokenize fails
            tokens = text.split()
        
        # 4. Remove stopwords and lemmatize
        cleaned_tokens = []
        for token in tokens:
            if token not in self.stop_words:
                try:
                    lemma = self.lemmatizer.lemmatize(token)
                except Exception:
                    lemma = token
                cleaned_tokens.append(lemma)
        
        return " ".join(cleaned_tokens)

    def find_match(self, user_query, threshold=0.18):
        if self.tfidf_matrix is None or not user_query:
            return None, 0.0

        # Preprocess user query
        processed_query = self.preprocess(user_query)
        if not processed_query.strip():
            # If query becomes empty (e.g. only stopwords/punctuation), match nothing
            return None, 0.0

        # Transform user query using the fitted TF-IDF vectorizer
        query_vector = self.vectorizer.transform([processed_query])

        # Calculate cosine similarity with all FAQ questions
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Find best match index and score
        best_match_idx = similarities.argsort()[-1]
        best_score = similarities[best_match_idx]

        if best_score >= threshold:
            return self.faqs[best_match_idx], float(best_score)
        
        return None, float(best_score)
