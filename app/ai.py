import json
import re
import urllib.request
import urllib.error
from flask import current_app

from .config import OPENROUTER_API_KEY


FREE_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "stepfun/step-3.5-flash:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]


def _clean_reply(text):
    """Elimina bloques de razonamiento interno que algunos modelos incluyen."""
    if not text:
        return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    lines = text.strip().split("\n")
    reasoning_keywords = ['okay', 'let me', 'the user', 'i need', 'i should', 'make sure',
                          'double-check', 'recall', 'remember', 'check if', 'yep', 'so the',
                          'just state', 'stick to', 'concisely']
    clean_lines = []
    in_reasoning = False
    for line in lines:
        low = line.lower().strip()
        if any(kw in low for kw in reasoning_keywords):
            in_reasoning = True
            continue
        if in_reasoning and not low:
            continue
        in_reasoning = False
        clean_lines.append(line)
    result = "\n".join(clean_lines).strip()
    return result if result else text.strip()


def openrouter_request(messages, max_tokens=300):
    if not OPENROUTER_API_KEY:
        return None
    for model in FREE_MODELS:
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENROUTER_API_KEY}"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                msg = result["choices"][0]["message"]
                reply = msg.get("content") or ""
                reply = _clean_reply(reply)
                if reply.strip():
                    current_app.logger.info("OpenRouter used model: %s", model)
                    return reply.strip()
        except urllib.error.HTTPError as e:
            current_app.logger.warning("Model %s failed: %s", model, e.code)
            continue
        except Exception as e:
            current_app.logger.warning("Model %s error: %s", model, e)
            continue
    return None


def openrouter_call(prompt, max_tokens=300):
    return openrouter_request([{"role": "user", "content": prompt}], max_tokens)


def review_is_clean(text):
    """Devuelve (True, None) si la reseña es válida, o (False, motivo) si no lo es."""
    if not OPENROUTER_API_KEY:
        return True, None
    prompt = f"""Eres un moderador de contenido para un videojuego. Analiza la siguiente reseña y determina si contiene:
- Insultos, lenguaje ofensivo, odio o contenido inapropiado
- Spam, texto sin sentido, caracteres aleatorios o contenido irrelevante

Reseña: "{text}"

Responde ÚNICAMENTE con JSON en este formato exacto, sin texto adicional:
{{"ok": true}} si la reseña es válida
{{"ok": false, "reason": "motivo breve en español"}} si no lo es"""
    reply = openrouter_call(prompt, max_tokens=80)
    if not reply:
        return True, None
    try:
        reply = reply.replace("```json", "").replace("```", "").strip()
        data = json.loads(reply)
        if data.get("ok"):
            return True, None
        return False, data.get("reason", "Contenido no permitido.")
    except Exception:
        return True, None
