# FAQ Chatbot

A small FAQ chatbot that preprocesses text, finds the most similar FAQ with TF-IDF cosine similarity, and returns the matching answer through a simple Flask chat UI.

## What it does

- Stores topic or product FAQs in `data/faqs.json`.
- Uses NLTK-style preprocessing: lowercasing, tokenization, punctuation cleanup, stop-word removal, and lemmatization.
- Uses scikit-learn TF-IDF plus cosine similarity when dependencies are installed.
- Falls back to a small built-in TF-IDF matcher if scikit-learn or NLTK is unavailable.
- Includes a browser chat UI and a command-line matcher.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m nltk.downloader punkt stopwords wordnet omw-1.4
```

## Run the chat UI

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Run from the command line

```powershell
python faq_engine.py "How do I track my shipment?"
```

## Customize the FAQ collection

Edit `data/faqs.json` and replace the sample ShopEase questions and answers with FAQs for your topic, product, or service. Each FAQ can include optional `tags`; tags are included in the searchable text to improve matching.

## Run tests

```powershell
python -m unittest discover -s tests
```
