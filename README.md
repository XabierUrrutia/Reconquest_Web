# Reconquest — Web App de Descarga

Aplicación Flask para alojar la página oficial de descarga del juego Reconquest.

## Estructura del proyecto

```
reconquest/
├── run.py                         ← Entry point local (python run.py)
├── app/                           ← Paquete Flask
│   ├── __init__.py                ← create_app() + app = create_app()
│   ├── config.py                  ← Variables de entorno y constantes
│   ├── db.py                      ← Conexión PostgreSQL y init_db
│   ├── decorators.py              ← login_required / admin_required
│   ├── utils.py                   ← Helpers (hash, detección SO…)
│   ├── email_utils.py             ← Envío SMTP
│   ├── ai.py                      ← Cliente OpenRouter
│   └── blueprints/
│       ├── main.py                ← /, /download, /api/version
│       ├── auth.py                ← /register /login /logout /forgot /reset
│       ├── admin.py               ← /admin/*, /api/stats
│       ├── reviews.py             ← /reviews/*, /admin/reviews/*
│       ├── profile.py             ← /profile, /profile/edit
│       ├── bugs.py                ← /api/bug, /admin/bug/*
│       └── chat.py                ← /api/chat, /api/free_models
├── requirements.txt               ← Dependencias Python
├── templates/                     ← Jinja2
├── static/
│   ├── img/logo.png
│   └── installer/
│       └── Reconquest_Setup_v1.0.0.exe   ← ⚠ COLOCA AQUÍ TU INSTALADOR
└── data/
```

## Instalación local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Colocar el instalador del juego
#    Copia tu .exe en:  static/installer/Reconquest_Setup_v1.0.0.exe

# 3. Arrancar el servidor
python run.py
#    → http://localhost:5000
```

## APIs disponibles

| Ruta           | Descripción                              |
|----------------|------------------------------------------|
| `GET /`        | Página principal                         |
| `GET /download`| Descarga el instalador + incrementa contador |
| `GET /api/stats`  | JSON con total de descargas           |
| `GET /api/version`| JSON con versión e info del instalador|

## Despliegue en producción (dominio propio)

### Opción A — Render.com (gratuito, fácil)
1. Sube el proyecto a GitHub
2. Crea una cuenta en https://render.com
3. "New Web Service" → conecta tu repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`  ← el paquete `app/` expone `app = create_app()` en su `__init__.py`
6. Listo. Render te da un dominio `.onrender.com` o puedes conectar el tuyo

### Opción B — VPS propio (Hetzner, DigitalOcean, etc.)
```bash
# En el servidor
sudo apt install python3-pip nginx certbot

pip install gunicorn flask
gunicorn --bind 0.0.0.0:8000 app:app &

# Nginx como proxy inverso
# Apunta tu dominio a la IP del servidor
# Usa certbot para HTTPS gratuito
```

### Opción C — PythonAnywhere (gratuito para proyectos pequeños)
1. Crea cuenta en https://www.pythonanywhere.com
2. Sube los archivos vía consola o interfaz web
3. Configura una Web App → Flask → apunta a `app.py`

## Añadir nueva versión del instalador

1. Cambia `GAME_VERSION` en `app/config.py`
2. Cambia `INSTALLER_WIN` / `INSTALLER_LNX` en `app/config.py`
3. Coloca el nuevo `.exe` en `static/installer/`
4. Reinicia el servidor
