import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

def ollama_generate_plan(prompt):
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code == 200:
        return response.json()["response"]
    else:
        return "Offline LLM not responding"
    