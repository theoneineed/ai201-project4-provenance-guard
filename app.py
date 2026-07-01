import uuid
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from signals import signal_1_llm, signal_2_stylometrics

app = Flask(__name__)

# --- Rate Limiter Setup ---
# Limit rationale: A real human writer submitting their original work to a platform 
# should realistically not need to submit more than 5 distinct pieces per minute. 
# 50 per day prevents bot flooding while generously accommodating power users.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

AUDIT_LOG_FILE = "audit_log.json"

def read_log():
    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_to_log(entry):
    log_data = read_log()
    log_data.append(entry)
    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=4)

def update_log_for_appeal(content_id, reasoning):
    log_data = read_log()
    updated = False
    for entry in log_data:
        if entry.get("content_id") == content_id:
            entry["status"] = "under_review"
            entry["appeal_reasoning"] = reasoning
            updated = True
            break
    
    if updated:
        with open(AUDIT_LOG_FILE, "w") as f:
            json.dump(log_data, f, indent=4)
    
    return updated

@app.route('/submit', methods=['POST'])
@limiter.limit("5 per minute; 50 per day")
def submit_content():
    data = request.get_json()
    text = data.get("text")
    creator_id = data.get("creator_id")
    
    if not text or not creator_id:
        return jsonify({"error": "Missing 'text' or 'creator_id'"}), 400

    content_id = str(uuid.uuid4())

    # 1. Fire Signals and Calculate Confidence
    llm_score = signal_1_llm(text)
    stylo_score = signal_2_stylometrics(text)
    final_confidence = round((0.6 * llm_score) + (0.4 * stylo_score), 2)

    # 2. Map exact Transparency Labels from planning.md
    if final_confidence >= 0.75:
        attribution = "likely_ai"
        label_text = "Automated Origin: This content closely matches the structural predictability and semantic coherence typical of AI-generated text."
    elif final_confidence <= 0.35:
        attribution = "likely_human"
        label_text = "Authentic Origin: This content reflects the natural variance and unique structural signatures of human writing."
    else:
        attribution = "uncertain"
        label_text = "Uncertain Origin: This content exhibits a mix of human idiosyncrasies and automated patterns. Attribution cannot be definitively confirmed."

    # 3. Create Audit Log Entry
    log_entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attribution": attribution,
        "confidence": final_confidence,
        "signal_1_llm": llm_score,
        "signal_2_stylo": stylo_score,
        "status": "classified"
    }
    write_to_log(log_entry)

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": final_confidence,
        "label": label_text
    })

@app.route('/appeal', methods=['POST'])
def appeal_content():
    data = request.get_json()
    content_id = data.get("content_id")
    reasoning = data.get("creator_reasoning")

    if not content_id or not reasoning:
        return jsonify({"error": "Missing 'content_id' or 'creator_reasoning'"}), 400

    success = update_log_for_appeal(content_id, reasoning)

    if success:
        return jsonify({
            "message": "Appeal logged successfully.",
            "status": "under_review"
        }), 200
    else:
        return jsonify({"error": "Content ID not found in audit log."}), 404

@app.route('/log', methods=['GET'])
def get_log():
    return jsonify({"entries": read_log()})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

