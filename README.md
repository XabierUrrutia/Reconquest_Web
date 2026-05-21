# Reconquest — Web App Oficial

Página web oficial del videojuego **Reconquest**, un RTS de un jugador ambientado en una ucronía histórica de Portugal en 1974. Desarrollado como Trabajo de Fin de Grado con Unity 6 y C#.

Esta aplicación Flask gestiona el registro de usuarios, la descarga del instalador, las reseñas, el soporte y el panel de administración.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3 · Flask · Gunicorn |
| Base de datos | PostgreSQL (Neon) |
| Autenticación | Sesiones Flask · bcrypt |
| Seguridad | Flask-WTF (CSRF) · Flask-Limiter |
| IA / Moderación | OpenRouter API |
| Frontend | HTML · CSS custom · Jinja2 (sin frameworks CSS externos) |
| Despliegue | Render.com |

---

## Características

- Página de presentación del juego con descarga directa (Windows / Linux)
- Registro e inicio de sesión con hashing bcrypt y migración automática de contraseñas antiguas
- Recuperación de contraseña por email (SMTP)
- Perfil de usuario editable (email, contraseña, avatar)
- Reseñas con moderación automática por IA (OpenRouter) y lista de palabras ofensivas
- Chatbot de soporte integrado
- Panel de administración: gestión de usuarios, reseñas, reportes de bugs y gráfico de descargas
- API de reportes de bugs para el cliente del juego
- Protección CSRF en todos los formularios y rate limiting en endpoints de API
- Tema día/noche persistente

---

## Estructura del proyecto

```
Renconquest_Web/
├── run.py                      ← Arranque local (python run.py)
├── requirements.txt
├── .env.example                ← Plantilla de variables de entorno
├── app/
│   ├── __init__.py             ← create_app() · CSRFProtect · Limiter
│   ├── config.py               ← Constantes y variables de entorno
│   ├── db.py                   ← Conexión PostgreSQL · init_db()
│   ├── decorators.py           ← login_required · admin_required
│   ├── extensions.py           ← Instancias de csrf y limiter
│   ├── utils.py                ← bcrypt · detección de SO · helpers
│   ├── email_utils.py          ← Envío SMTP para reset de contraseña
│   ├── ai.py                   ← Cliente OpenRouter
│   ├── moderation.py           ← Lista de palabras bloqueadas
│   └── blueprints/
│       ├── main.py             ← / · /download · /api/version
│       ├── auth.py             ← /register · /login · /logout · /forgot · /reset
│       ├── admin.py            ← /admin · /api/stats · /api/admin/downloads_chart
│       ├── reviews.py          ← /reviews/submit · /admin/reviews/*
│       ├── profile.py          ← /profile · /profile/edit
│       ├── bugs.py             ← /api/bug · /admin/bug/*
│       └── chat.py             ← /api/chat · /api/free_models
├── templates/                  ← Jinja2 (base.html + páginas)
└── static/
    ├── css/main.css
    ├── img/
    └── installer/              ← ⚠ Ignorado en git (ver GitHub Releases)
```

---

## Configuración local

### Prerrequisitos

- Python 3.10+
- Acceso a un PostgreSQL (p.ej. Neon en local o en la nube)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/XabierUrrutia/Renconquest_Web.git
cd Renconquest_Web

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus valores

# 4. Arrancar el servidor
python run.py
# → http://localhost:5000
```

### Variables de entorno

Copia `.env.example` a `.env` y rellena los valores. El archivo `.env` **nunca** se sube a git.

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | URL de conexión PostgreSQL (ej. Neon) |
| `SECRET_KEY` | **Sí en producción** | Clave de sesión Flask. Sin ella las sesiones mueren en cada reinicio |
| `ADMIN_PASSWORD` | No | Password del admin creado en `init_db`. Si no se configura se genera aleatoriamente y se imprime **una sola vez** en los logs |
| `OPENROUTER_API_KEY` | No | Clave de OpenRouter para chatbot y moderación por IA. Sin ella, el chatbot se deshabilita y la moderación es solo por lista de palabras |
| `SMTP_HOST` | No | Servidor SMTP para emails de reset (defecto: smtp.gmail.com) |
| `SMTP_PORT` | No | Puerto SMTP (defecto: 587) |
| `SMTP_USER` | No | Usuario SMTP |
| `SMTP_PASS` | No | Contraseña SMTP |
| `SITE_URL` | No | URL base para links en emails (defecto: http://localhost:5000) |

> **Modo dev sin SMTP:** si no configuras SMTP, los emails de reset no se enviarán. Configura las variables `SMTP_*` para habilitar la recuperación de contraseña.

---

## Despliegue en Render + Neon

### Base de datos — Neon

1. Crea un proyecto en [neon.tech](https://neon.tech)
2. Copia la **Connection string** (incluye `sslmode=require` automáticamente)
3. Úsala como valor de `DATABASE_URL`

El schema se crea automáticamente en el primer arranque con `init_db()`.

### Web Service — Render

1. Conecta el repositorio en [render.com](https://render.com) → *New Web Service*
2. Configura:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
3. Añade las variables de entorno en *Environment*:
   - `DATABASE_URL` → connection string de Neon
   - `SECRET_KEY` → string aleatorio largo (p.ej. `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `ADMIN_PASSWORD` → password para el primer acceso al panel
   - El resto según necesites (SMTP, OpenRouter…)

---

## API Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET` | `/` | — | Página principal |
| `GET` | `/download` | Login | Descarga instalador + registra evento |
| `GET` | `/api/version` | — | Versión actual del juego |
| `POST` | `/api/bug` | — | Enviar reporte de bug (5 req/min) |
| `POST` | `/api/chat` | — | Chat con asistente IA (20 req/min) |
| `GET` | `/api/stats` | Admin | Estadísticas totales |
| `GET` | `/api/admin/downloads_chart` | Admin | Datos del gráfico de descargas |
| `GET` | `/api/free_models` | Admin | Modelos gratuitos disponibles en OpenRouter |

---

## Seguridad

- Contraseñas hasheadas con **bcrypt** (migración automática desde SHA256 en el primer login)
- **CSRF tokens** en todos los formularios HTML
- **Rate limiting** en endpoints de API públicos
- Avatar URL validada (solo `http://https://`, sin SVG, máximo 512 caracteres)
- Moderación de reseñas por IA + lista de palabras bloqueadas

---

## Licencia

Proyecto académico — Trabajo de Fin de Grado · 2025
