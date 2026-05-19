"""Dev entry point. En producción (Render) se usa `gunicorn app:app`."""
from dotenv import load_dotenv
load_dotenv()

from app import app
from app.db import init_db


if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        print(f"[WARN] No se pudo conectar a la BD: {e}")
        print("[WARN] La app arranca igualmente, pero las rutas que usen la BD fallarán.")
    app.run(debug=True, host="0.0.0.0", port=5000)
