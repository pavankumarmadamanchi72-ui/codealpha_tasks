from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from faq_engine import FAQMatcher


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "faqs.json"

app = Flask(__name__)
matcher = FAQMatcher.from_json(DATA_PATH)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/ask")
def ask():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    return jsonify(matcher.answer(question))


@app.get("/api/faqs")
def faqs():
    return jsonify(
        [
            {
                "question": faq.question,
                "answer": faq.answer,
                "tags": list(faq.tags),
            }
            for faq in matcher.faqs
        ]
    )


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(debug=debug, host="127.0.0.1", port=5000)
