# SocialGenius AI

Chatbot de IA que analiza negocios y genera estrategias de contenido para Instagram y TikTok. Calendario editorial semanal, ideas de contenido por industria, copywriting optimizado, horarios de publicacion y hashtags.

## Stack Tecnologico

### Frontend
| Tecnologia | Uso |
|---|---|
| Next.js 14 | Framework React (App Router) |
| React 18 | Libreria UI |
| TypeScript | Tipado estatico |
| TailwindCSS | Estilos utility-first |
| shadcn/ui | Componentes UI |
| SSE | Streaming del chat en tiempo real |

### Backend
| Tecnologia | Uso |
|---|---|
| FastAPI | Framework web async |
| Python 3.12 | Lenguaje del servidor |
| Uvicorn | Servidor ASGI |
| Pydantic v2 | Validacion de datos y settings |

### Base de Datos
| Tecnologia | Uso |
|---|---|
| SQLite | BD relacional (desarrollo) |
| SQLAlchemy 2.0 | ORM async con aiosqlite |
| Alembic | Migraciones de esquema |

### Inteligencia Artificial
| Tecnologia | Uso |
|---|---|
| Hugging Face Inference API | Proveedor de IA (gratuito) |
| Llama 3.2 3B Instruct | Modelo de lenguaje |
| InferenceClient | SDK de HuggingFace |

### Autenticacion
| Tecnologia | Uso |
|---|---|
| JWT | Access + Refresh tokens |
| passlib + bcrypt | Hashing de contrasenas |

## Requisitos

- Node.js 18+
- Python 3.12+
- Token de Hugging Face (gratuito)

## Instalacion

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

Crear archivo `backend/.env`:

```env
DATABASE_URL=sqlite+aiosqlite:///./socialgenius.db
SYNC_DATABASE_URL=sqlite:///./socialgenius.db
JWT_SECRET_KEY=tu-clave-secreta
HUGGINGFACE_API_KEY=tu-token-de-huggingface
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-3B-Instruct
```

Ejecutar migraciones y levantar:

```bash
cd backend
source venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Abrir http://localhost:3000

## Estructura del Proyecto

```
SocialGenius-AI/
├── frontend/                # Next.js 14
│   └── src/
│       ├── app/             # App Router (pages)
│       │   └── (dashboard)/ # Route group con layout
│       │       ├── businesses/
│       │       ├── calendar/
│       │       ├── chat/
│       │       └── content/
│       ├── components/ui/   # shadcn/ui
│       ├── contexts/        # AuthProvider
│       ├── hooks/           # useChat, useAuth
│       └── lib/             # API client, utils
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── api/             # Routes/endpoints
│   │   ├── ai/              # Motor de IA
│   │   │   └── prompts/     # Prompts por tipo de conversacion
│   │   ├── core/            # Constants, exceptions
│   │   ├── db/              # Conexion a BD
│   │   ├── models/          # SQLAlchemy models
│   │   └── services/        # Logica de negocio
│   └── alembic/             # Migraciones
└── README.md
```

## Stack de Produccion (futuro)

| Desarrollo | Produccion |
|---|---|
| SQLite | PostgreSQL |
| HuggingFace (gratis) | OpenAI / Anthropic |
| - | Redis (cache/sesiones) |
| Stripe test mode | Stripe live |
