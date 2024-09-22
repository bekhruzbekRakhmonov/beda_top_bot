import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))


def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    return [lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in stop_words]


def get_intent(text):
    preprocessed = preprocess_text(text)
    if any(word in preprocessed for word in ['document', 'prepare', 'contract']):
        return 'prepare_document'
    elif any(word in preprocessed for word in ['onboard', 'new', 'client']):
        return 'client_onboarding'
    elif any(word in preprocessed for word in ['search', 'find', 'property']):
        return 'property_search'
    elif any(word in preprocessed for word in ['market', 'analysis', 'trend']):
        return 'market_analysis'
    elif any(word in preprocessed for word in ['client', 'info', 'information']):
        return 'client_info'
    else:
        return 'general_query'
