import json
import re
import urllib.request
import urllib.error
from flask import current_app

from .config import OPENROUTER_API_KEY


FREE_MODELS = [
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-3-4b-it:free",
    "stepfun/step-3.5-flash:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]


_THINK_TAGS = re.compile(
    r"<\s*(think|thinking|thought|reasoning|reflection|scratchpad|analysis)\s*>.*?"
    r"<\s*/\s*\1\s*>",
    flags=re.DOTALL | re.IGNORECASE,
)

_FINAL_ANSWER_MARKERS = [
    "final answer:", "respuesta final:", "respuesta:", "answer:",
    "final:", "salida:", "output:", "assistant:",
]

_REASONING_LINE_KEYWORDS = (
    "okay", "let me", "the user", "i need", "i should", "make sure",
    "double-check", "recall", "remember", "check if", "yep", "so the",
    "just state", "stick to", "concisely", "i'll ", "i will ",
    "wait,", "hmm", "actually,", "first,", "then,", "let's ",
)


def _clean_reply(text):
    """Elimina razonamiento interno, etiquetas de thinking y prefijos antes de la respuesta."""
    if not text:
        return ""

    text = _THINK_TAGS.sub("", text)

    text = re.sub(r"\[\s*(think|thinking|reasoning)\s*\].*?\[\s*/\s*\1\s*\]",
                  "", text, flags=re.DOTALL | re.IGNORECASE)

    low = text.lower()
    for marker in _FINAL_ANSWER_MARKERS:
        idx = low.rfind(marker)
        if idx != -1:
            text = text[idx + len(marker):]
            low = text.lower()

    lines = text.strip().split("\n")
    clean_lines = []
    in_reasoning = False
    for line in lines:
        stripped = line.strip()
        low_line = stripped.lower()
        if not stripped:
            if not in_reasoning:
                clean_lines.append(line)
            continue
        if any(kw in low_line for kw in _REASONING_LINE_KEYWORDS):
            in_reasoning = True
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
            "max_tokens": max_tokens,
            "reasoning": {"exclude": True},
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
    """Modera vía IA.
    Devuelve (ok: bool, reason: str|None, api_ok: bool):
      - ok=True, api_ok=True  → la IA dijo que está limpio
      - ok=False, api_ok=True → la IA lo rechazó, reason tiene el motivo
      - ok=True, api_ok=False → la IA no pudo clasificar (fail-open)
    """
    if not OPENROUTER_API_KEY:
        return True, None, False
    prompt = f"""Eres un moderador de contenido para un videojuego. Analiza la siguiente reseña y determina si contiene:
- Insultos, lenguaje ofensivo, odio o contenido inapropiado
- Spam, texto sin sentido, caracteres aleatorios o contenido irrelevante

Reseña: "{text}"

Responde ÚNICAMENTE con JSON en este formato exacto, sin texto adicional:
{{"ok": true}} si la reseña es válida
{{"ok": false, "reason": "motivo breve en español"}} si no lo es"""
    reply = openrouter_call(prompt, max_tokens=80)
    if not reply:
        return True, None, False
    try:
        reply = reply.replace("```json", "").replace("```", "").strip()
        data = json.loads(reply)
        if data.get("ok"):
            return True, None, True
        return False, data.get("reason", "Contenido no permitido."), True
    except Exception as e:
        current_app.logger.warning("review_is_clean parse error: %s (reply=%r)", e, reply)
        return True, None, False
