import os
from flask import Flask, render_template, request, jsonify
from nlp_engine import FAQBot

app = Flask(__name__)

# Initialize the FAQ Bot
FAQ_DATA_PATH = os.path.join(os.path.dirname(__file__), 'faq_data.json')
bot = FAQBot(FAQ_DATA_PATH)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/faqs', methods=['GET'])
def get_faqs():
    # Return grouped FAQs for the sidebar
    grouped = {}
    for faq in bot.faqs:
        cat = faq['category']
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({
            "id": faq["id"],
            "question": faq["question"],
            "suggestions": faq["suggestions"]
        })
    return jsonify(grouped)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({
            "status": "error",
            "message": "Message content is empty."
        }), 400
        
    match, score = bot.find_match(user_message)
    
    if match:
        return jsonify({
            "status": "success",
            "match": True,
            "id": match["id"],
            "category": match["category"],
            "question": match["question"],
            "answer": match["answer"],
            "score": score,
            "suggestions": match["suggestions"]
        })
    else:
        # Fallback suggestions from top FAQs
        default_suggestions = [
            "How do I set up my Aura Smart Home Hub for the first time?",
            "Does Aura integrate with Google Assistant and Amazon Alexa?",
            "How does Aura protect my smart home data and privacy?"
        ]
        return jsonify({
            "status": "success",
            "match": False,
            "answer": "I'm sorry, I couldn't find a close match for that question. Could you please rephrase it? You can also ask about these popular topics:",
            "score": score,
            "suggestions": default_suggestions
        })

if __name__ == '__main__':
    # Using port 5000 by default
    app.run(debug=True, host='127.0.0.1', port=5000)
