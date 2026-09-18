from flask import Flask, render_template, request, jsonify
from chatbot import get_response

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"reply": "Please ask a car-related question."})
    try:
        return jsonify({"reply": get_response(message)})
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"reply": "Sorry, something went wrong. Check your Gemini API key and terminal."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
