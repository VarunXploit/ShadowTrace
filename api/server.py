# D:\Hackathon\api\server.py
from flask import Flask, request, jsonify
from flask_cors import CORS

from backend.service import (
    check_text_service,
    check_account_service,
    check_username_service,
)

app = Flask(__name__)

# Allow React dev servers on common ports (add more if needed)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173"]}})

@app.post("/api/check-text")
def api_check_text():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    result = check_text_service(text)
    return jsonify(result), 200

@app.post("/api/check-account")
def api_check_account():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    result = check_account_service(name)
    return jsonify(result), 200

@app.post("/api/check-username")
def api_check_username():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    result = check_username_service(username)
    return jsonify(result), 200

if __name__ == "__main__":
    # Debug=True for development. Change host/port if you want externally accessible.
    app.run(host="127.0.0.1", port=5000, debug=True)
