# Prompt Jar 🫙✨

A small Flask app that uses a local Gemma model through Ollama to turn creative preferences into a single art & craft prompt.

## Features

- Choose art type, topic, colors, supplies, and time
- Use freeform inputs or “Surprise me”
- Save and delete prompts locally

## Setup

1. Install **Python 3.11+** and **Ollama**.

2. Download Gemma:

```bash
ollama pull gemma3:1b
```

3. Create the environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

4. Start Prompt Jar:

```bash
python app.py
```

5. Open **http://localhost:5000**

Keep Ollama running while generating ideas.

## How It Works

```text
Browser → Flask → Ollama / Gemma → JSON idea
```

Saved prompts are stored locally in `data/prompts.json`. Each generated and saved idea contains only its prompt text.
