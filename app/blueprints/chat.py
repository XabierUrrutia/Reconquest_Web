import json
import urllib.request
from flask import Blueprint, request, jsonify

from ..config import OPENROUTER_API_KEY
from ..decorators import admin_required
from ..extensions import csrf, limiter
from ..ai import openrouter_request


bp = Blueprint("chat", __name__)


SYSTEM_PROMPT = """Eres el asistente de soporte oficial de Reconquest, un videojuego RTS gratuito.

Información clave:
- Género: Estrategia en tiempo real (RTS), un jugador
- Ambientación: Ucronía histórica en Portugal — la Revolución de los Claveles de 1974 fracasó y desencadena una guerra civil ficticia
- El jugador conquista fábricas para obtener recursos, gestiona tropas y captura sectores hasta destruir la base enemiga
- Completamente GRATUITO. Requiere registro para descargar
- Disponible para Windows 10/11 (64-bit) y Linux (64-bit). No hay versión para macOS ni móviles
- Requisitos Windows: 4 GB RAM, DirectX 11, ~500 MB de disco
- Requisitos Linux: 4 GB RAM, OpenGL 3.2+/Vulkan, ~500 MB de disco
- Si Windows SmartScreen alerta, es un falso positivo. Clic en "Más información → Ejecutar de todas formas"
- Desarrollado con Unity 6 y C# como Trabajo de Fin de Grado
- No tiene multijugador
- Para recuperar contraseña: ir a /forgot en la web

Responde siempre en español, de forma concisa y amigable. Si no sabes algo, di que contacten con el desarrollador. No inventes información.
IMPORTANTE: Responde SOLO con el mensaje final en español. No muestres razonamiento interno, pasos previos, texto entre asteriscos ni etiquetas. Solo la respuesta directa y concisa, sin formato markdown."""


@bp.route("/api/chat", methods=["POST"])
@csrf.exempt
@limiter.limit("20 per minute")
def api_chat():
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "Chatbot no configurado."}), 503

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    if not messages or not isinstance(messages, list):
        return jsonify({"error": "Petición inválida."}), 400

    messages = messages[-10:]

    or_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in messages:
        or_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    reply = openrouter_request(or_messages, max_tokens=300)
    if reply:
        return jsonify({"reply": reply})
    return jsonify({"error": "El asistente no está disponible ahora mismo. Inténtalo más tarde."}), 503


@bp.route("/api/free_models")
@admin_required
def api_free_models():
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            free = [m["id"] for m in result.get("data", []) if ":free" in m["id"]]
            return jsonify({"free_models": free})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
