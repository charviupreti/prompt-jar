import json
import os
import re
import uuid
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_FILE = DATA_DIR / "prompts.json"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")


def ensure_data_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PROMPTS_FILE.exists():
        PROMPTS_FILE.write_text("[]", encoding="utf-8")


def load_saved_prompts():
    ensure_data_file()
    try:
        data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def save_prompt(prompt_data):
    prompts = load_saved_prompts()
    payload = prompt_data if isinstance(prompt_data, dict) else {}
    prompt_text = str(payload.get("prompt", "")).strip()
    if not prompt_text:
        return prompts
    safe_prompt = {
        "id": str(payload.get("id") or f"idea-{uuid.uuid4().hex[:8]}"),
        "prompt": prompt_text,
    }
    prompts.insert(0, safe_prompt)
    ensure_data_file()
    PROMPTS_FILE.write_text(json.dumps(prompts, indent=2), encoding="utf-8")
    return prompts


def delete_prompt(prompt_id):
    prompt_id = str(prompt_id or "").strip()
    prompts = [
        item for item in load_saved_prompts() if str(item.get("id")) != prompt_id
    ]
    ensure_data_file()
    PROMPTS_FILE.write_text(json.dumps(prompts, indent=2), encoding="utf-8")
    return prompts


def extract_json_object(raw_text):
    if not raw_text:
        raise ValueError("No content returned from Ollama")

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def call_ollama(form_input):
    output_schema = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
        },
        "required": ["prompt"],
        "additionalProperties": False,
    }
    prompt = (
        "Make one short art or craft idea from these preferences. "
        'Return only JSON: {"prompt":"..."}. '
        f"{form_input.get('what', 'Surprise me')}, "
        f"{form_input.get('topic', 'Surprise me')}, "
        f"{form_input.get('colors', 'Surprise me')}, "
        f"{form_input.get('supplies', 'Surprise me')}, "
        f"{form_input.get('time', '30 minutes')}, "
        f"{form_input.get('intensity', 'default')} mode. "
        "If supplies are not 'Surprise me': "
        "USE ONLY THESE SUPPLIES. "
        "DO NOT USE ANY OTHER MATERIAL. "
        "DO NOT INVENT MATERIALS. "
        "Make it fit the time. "
        "Beginner = simple. "
        "Weird = silly or unusual. "
        "Give only the idea. No labels or extra text."
    )
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": output_schema,
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    raw_text = payload.get("response", "")
    result = extract_json_object(raw_text)

    if not isinstance(result, dict):
        raise ValueError("Unexpected response shape from Ollama")

    prompt_text = result.get("prompt")
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise ValueError("Ollama response is missing a prompt")
    return {"prompt": prompt_text.strip()}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(call_ollama(payload))
    except requests.RequestException:
        return (
            jsonify({"error": "Ollama is unavailable. Start Ollama and try again."}),
            503,
        )
    except (ValueError, TypeError, KeyError):
        return (
            jsonify({"error": "Ollama returned an invalid idea. Please try again."}),
            502,
        )


@app.route("/api/prompts", methods=["GET"])
def api_prompts_get():
    return jsonify(load_saved_prompts())


@app.route("/api/prompts", methods=["POST"])
def api_prompts_post():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict) or not str(payload.get("prompt", "")).strip():
        return jsonify({"error": "A prompt is required."}), 400
    prompts = save_prompt(payload)
    if not prompts:
        return jsonify({"error": "A prompt is required."}), 400
    return jsonify({"saved": prompts[0], "count": len(prompts)})


@app.route("/api/prompts", methods=["DELETE"])
def api_prompts_delete():
    payload = request.get_json(silent=True) or {}
    prompt_id = payload.get("id") or request.args.get("id")
    remaining = delete_prompt(prompt_id)
    return jsonify({"deleted": bool(prompt_id), "prompts": remaining})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
