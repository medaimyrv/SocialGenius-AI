# SocialGenius AI

Asistente de estrategia de contenido en redes sociales potenciado por inteligencia artificial, diseñado para pequeños negocios. Genera estrategias, calendarios de contenido semanales y copywriting optimizado para Instagram y TikTok mediante conversaciones naturales.

---

## Tabla de Contenidos

- [Stack Tecnológico](#stack-tecnológico)
- [Modelos de IA](#modelos-de-ia)
- [Sistema RAG](#sistema-rag)
- [Base de Datos](#base-de-datos)
- [API REST](#api-rest)
- [Despliegue](#despliegue)
- [Variables de Entorno](#variables-de-entorno)
- [Instalación Local](#instalación-local)

---

## Stack Tecnológico

### Frontend

| Tecnología | Versión | Uso |
|---|---|---|
| **Next.js** | 14.2.35 | Framework React con App Router |
| **React** | 18.x | UI library |
| **TypeScript** | 5.x | Tipado estático |
| **Tailwind CSS** | 3.4.1 | Estilos utilitarios (dark mode) |
| **shadcn/ui** | — | Componentes accesibles (Radix UI) |
| **Lucide React** | 0.563.0 | Iconografía |

**Comunicación con el backend:**
- API client con JWT — renovación automática del access token en respuestas 401
- **Server-Sent Events (SSE)** para streaming del chat en tiempo real
- `AbortController` para cancelar streams activos
- Tokens almacenados en `localStorage` (access: 30 min / refresh: 7 días)

---

### Backend

| Tecnología | Versión | Uso |
|---|---|---|
| **FastAPI** | 0.133.1 | Framework API async |
| **Python** | 3.12 | Lenguaje principal |
| **Uvicorn** | 0.41.0 | Servidor ASGI |
| **Pydantic v2** | 2.12.5 | Validación de datos y settings |
| **SQLAlchemy** | 2.0.47 | ORM async |
| **Alembic** | 1.18.4 | Migraciones de base de datos |
| **asyncpg** | 0.31.0 | Driver async para PostgreSQL |
| **aiosqlite** | 0.22.1 | Driver async para SQLite (dev local) |
| **passlib + bcrypt** | 1.7.4 / 4.3.0 | Hashing de contraseñas |
| **python-jose** | 3.5.0 | JWT tokens |
| **httpx** | 0.28.1 | Cliente HTTP async (llamadas a HuggingFace) |
| **pypdf** | 6.9.1 | Extracción de texto de PDFs |
| **stripe** | 14.4.0 | Pagos y suscripciones |
| **sentry-sdk** | 2.53.0 | Monitoreo de errores en producción |

---

## Modelos de IA

Todos los modelos se consumen a través de la **HuggingFace Inference API** (sin instalación local de pesos).

### Modelo de Chat / Generación de Texto

| Propiedad | Valor |
|---|---|
| **Modelo** | `Qwen/Qwen2.5-72B-Instruct` |
| **Proveedor** | HuggingFace Inference API |
| **Cliente** | `AsyncInferenceClient` (huggingface_hub) |
| **Temperatura** | 0.7 |
| **Max tokens** | 2048 |
| **Streaming** | Sí — SSE chunks en tiempo real |
| **Idioma de respuesta** | Español |

### Modelo de Embeddings (RAG)

| Propiedad | Valor |
|---|---|
| **Modelo** | `intfloat/multilingual-e5-small` |
| **Proveedor** | HuggingFace Inference API |
| **Dimensiones del vector** | 384 |
| **Método de llamada** | HTTP POST async via `httpx` |
| **Endpoint** | `https://api-inference.huggingface.co/models/intfloat/multilingual-e5-small` |

Modelo entrenado específicamente en texto multilingüe (incluye español), con mejor precisión semántica que alternativas en inglés. Requiere el protocolo de prefijos E5:

| Contexto | Prefijo aplicado |
|---|---|
| Indexar documentos y mensajes | `passage: <texto>` |
| Consulta de búsqueda del usuario | `query: <texto>` |

> No se instalan modelos de embeddings localmente. Ninguna dependencia ML pesada (torch, ONNX, CUDA) en el servidor.

### Prompts Especializados

El sistema cuenta con **6 tipos de conversación**, cada uno con su propio system prompt:

| Tipo | Descripción |
|---|---|
| `BUSINESS_ANALYSIS` | Análisis profundo del negocio y su presencia digital |
| `CONTENT_STRATEGY` | Estrategia de contenido personalizada para la marca |
| `CALENDAR_CREATION` | Genera un calendario semanal completo (auto-parseado y guardado en DB) |
| `COPYWRITING` | Redacción de copies optimizados por plataforma |
| `HASHTAG_RESEARCH` | Investigación de hashtags relevantes y tendencias |
| `GENERAL` | Chat general con contexto de negocio |

Cada prompt se construye con el método `.build(business)` inyectando: nombre, industria, descripción, audiencia objetivo, tono de voz y redes sociales del negocio.

---

## Sistema RAG

**RAG (Retrieval-Augmented Generation)** permite al asistente responder usando documentos propios del negocio como fuente de conocimiento adicional.

### Flujo completo

```
Usuario sube PDF / TXT (máx 10 MB)
           │
           ▼
   Extracción de texto
   (pypdf para PDF, lectura directa para TXT)
           │
           ▼
   Chunking por palabras
   (ventana deslizante, 500 palabras, solapamiento 50)
           │
           ▼
   HuggingFace Embedding API
   (sentence-transformers/all-MiniLM-L6-v2 → vector 384 dims)
           │
           ▼
   Almacenamiento en tabla rag_chunks
   (JSONB en PostgreSQL / TEXT-JSON en SQLite)
           │
           ▼
   En cada mensaje del chat:
   Query → Embedding → Similitud Coseno → Top-5 chunks
           │
           ▼
   Chunks inyectados en el system prompt antes del LLM
           │
           ▼
   Respuesta contextualizada del modelo
```

### Parámetros de configuración

| Parámetro | Valor | Descripción |
|---|---|---|
| `CHUNK_MAX_WORDS` | 300 palabras | Máximo de palabras por chunk (agrupando oraciones completas) |
| `CHUNK_OVERLAP_SENTENCES` | 2 oraciones | Oraciones que se solapan entre chunks consecutivos |
| `TOP_K` | 5 | Chunks más relevantes recuperados por búsqueda |
| Mínimo de oración | 15 caracteres | Fragmentos más cortos se descartan |

**Estrategia de chunking:** se divide el texto en oraciones (respetando `.`, `!`, `?` como límites) y luego se agrupan hasta llenar `CHUNK_MAX_WORDS`. El solapamiento se hace a nivel de oración entera, nunca en medio de una frase. Esto preserva el contexto semántico completo en cada chunk.

### Almacenamiento de vectores

No se utiliza base de datos vectorial externa. Los embeddings se almacenan directamente en la tabla `rag_chunks` de PostgreSQL usando la columna `embedding`:

| Entorno | Tipo de columna | Implementación |
|---|---|---|
| **PostgreSQL** (producción) | `JSONB` | JSON binario nativo de Postgres |
| **SQLite** (desarrollo) | `TEXT` | JSON serializado como texto |

La detección del tipo es automática vía el `TypeDecorator` de SQLAlchemy `EmbeddingType`.

### Búsqueda por similitud semántica

Sin pgvector ni extensiones externas. La similitud se calcula en Python puro:

```python
def _cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (norm(a) * norm(b))
```

Se cargan todos los chunks del negocio, se puntúan y se retornan los `TOP_K` más similares al query.

### Fuentes indexadas

| `source_type` | Descripción |
|---|---|
| `document` | Chunks de PDFs o TXTs subidos por el usuario |
| `message` | Mensajes del historial de conversaciones (también se indexan) |

---

## Base de Datos

### Motor por entorno

| Entorno | Base de Datos | Driver |
|---|---|---|
| Desarrollo local | SQLite | `aiosqlite` |
| Producción (Railway) | PostgreSQL 17 | `asyncpg` |

La detección es automática: si `DATABASE_URL` contiene `postgresql`, se usa `asyncpg`; si contiene `sqlite`, se usa `aiosqlite`. El `SYNC_DATABASE_URL` (para Alembic) se deriva automáticamente.

### Modelos / Tablas

#### `users`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `email` | VARCHAR(255) UNIQUE | Correo electrónico |
| `hashed_password` | VARCHAR(255) | Contraseña hasheada con bcrypt |
| `full_name` | VARCHAR(255) | Nombre completo (nullable) |
| `is_active` | BOOL | Si `false`, impide el login (soft delete) |
| `is_verified` | BOOL | Verificación de email |
| `role` | VARCHAR(20) | `user` o `admin` |
| `stripe_customer_id` | VARCHAR(255) UNIQUE | ID de cliente en Stripe |

#### `businesses`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | — |
| `owner_id` | FK → users | Propietario |
| `name` | VARCHAR | Nombre del negocio |
| `industry` | VARCHAR | Industria/rubro |
| `description` | TEXT | Descripción del negocio |
| `target_audience` | TEXT | Audiencia objetivo |
| `brand_voice` | TEXT | Tono y voz de marca |
| `website_url` | VARCHAR | URL del sitio web |
| `instagram_handle` | VARCHAR | @usuario de Instagram |
| `tiktok_handle` | VARCHAR | @usuario de TikTok |
| `extra_context` | JSON | Contexto adicional libre |

#### `conversations`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | — |
| `user_id` | FK → users | — |
| `business_id` | FK → businesses | Negocio asociado (nullable) |
| `title` | VARCHAR | Título de la conversación |
| `conversation_type` | ENUM | 6 tipos especializados (ver modelos de IA) |
| `is_archived` | BOOL | Estado de archivo |

#### `messages`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | — |
| `conversation_id` | FK → conversations | — |
| `role` | ENUM | `user`, `assistant`, `system` |
| `content` | TEXT | Contenido del mensaje |
| `token_count` | INT | Tokens utilizados |
| `model_used` | VARCHAR | Modelo que generó la respuesta |

#### `content_calendars`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | — |
| `business_id` | FK → businesses | — |
| `conversation_id` | FK → conversations | Conversación que lo originó |
| `title` | VARCHAR | Título del calendario |
| `week_start_date` / `week_end_date` | DATE | Semana del calendario |
| `platform` | VARCHAR | Plataforma principal |
| `strategy_summary` | TEXT | Resumen de la estrategia |
| `status` | VARCHAR | `draft` o `published` |

#### `content_pieces`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | — |
| `calendar_id` | FK → content_calendars | — |
| `platform` | VARCHAR | Instagram / TikTok |
| `content_format` | ENUM | Reel, Carousel, Single Image, Story, TikTok Video, Live |
| `topic` | VARCHAR | Tema del post |
| `caption` | TEXT | Texto del post |
| `hashtags` | JSON | Lista de hashtags |
| `visual_description` | TEXT | Descripción visual para el diseñador |
| `hook` | TEXT | Gancho inicial |
| `call_to_action` | TEXT | CTA al final |
| `scheduled_date` | DATE | Fecha programada |
| `scheduled_time` | TIME | Hora programada |
| `day_of_week` | VARCHAR | Día de la semana |
| `status` | VARCHAR | `draft` o `published` |

#### `subscriptions`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | — |
| `user_id` | FK → users UNIQUE | Un usuario = una suscripción |
| `plan_tier` | ENUM | `FREE` o `PRO` |
| `status` | ENUM | `ACTIVE`, `CANCELED`, `PAST_DUE`, `INACTIVE` |
| `stripe_subscription_id` | VARCHAR | ID en Stripe |
| `strategies_used_this_month` | INT | Contador mensual de estrategias |
| `calendars_used_this_month` | INT | Contador mensual de calendarios |
| `messages_used_this_month` | INT | Contador mensual de mensajes |
| `usage_reset_date` | DATE | Fecha de reset del ciclo |

#### `documents`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | — |
| `business_id` | FK → businesses | — |
| `user_id` | FK → users | — |
| `filename` | VARCHAR | Nombre del archivo original |
| `content_type` | VARCHAR | MIME type |
| `text_content` | TEXT | Texto extraído (máx 50k caracteres) |
| `chunk_count` | INT | Número de chunks indexados en RAG |

#### `rag_chunks`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | — |
| `business_id` | FK → businesses | Negocio propietario |
| `source_type` | VARCHAR | `document` o `message` |
| `source_id` | VARCHAR | ID del documento o conversación |
| `filename` | VARCHAR | Nombre del archivo (solo para documents) |
| `chunk_index` | INT | Posición del chunk en el documento |
| `role` | VARCHAR | `user` o `assistant` (solo para messages) |
| `content` | TEXT | Texto del chunk |
| `embedding` | **JSONB** / TEXT | Vector de **384 dimensiones** (float list) |

#### `user_activities`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | — |
| `user_id` | FK → users | — |
| `event_type` | VARCHAR | Tipo de evento |
| `metadata_` | JSON | Contexto adicional del evento |

**Eventos registrados:** `login`, `register`, `new_conversation`, `send_message`, `calendar_created`, `strategy_generated`, `business_created`, `business_updated`, `business_deleted`

### Cascadas de eliminación

```
users → businesses       → content_calendars → content_pieces
      → conversations    → messages
      → subscriptions
      → documents        → rag_chunks
      → user_activities
```

Todos los modelos hijos tienen `CASCADE DELETE` desde `users`.

### Migraciones

Gestionadas con **Alembic**. En producción se ejecutan automáticamente al arrancar antes del servidor:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## API REST

**Base URL:** `/api/v1`

### Autenticación

```
POST  /auth/register        Registrar usuario
POST  /auth/login           Login → access token + refresh token
POST  /auth/refresh         Renovar access token
GET   /auth/me              Perfil del usuario actual
```

### Negocios

```
GET    /businesses           Listar negocios del usuario
POST   /businesses           Crear negocio
GET    /businesses/{id}      Detalle
PATCH  /businesses/{id}      Actualizar
DELETE /businesses/{id}      Eliminar
```

### Conversaciones

```
GET    /conversations        Listar (filtros: business_id, type)
POST   /conversations        Crear
GET    /conversations/{id}   Detalle con mensajes
PATCH  /conversations/{id}   Actualizar (título, is_archived)
DELETE /conversations/{id}   Eliminar
```

### Chat — Streaming SSE

```
POST  /chat/{conversation_id}/messages
```

Responde con `StreamingResponse` en formato SSE:

```
data: {"content": "Hola, "}
data: {"content": "te ayudo con..."}
data: {"done": true}
```

### Documentos RAG

```
POST   /documents/{business_id}             Subir PDF o TXT (máx 10 MB)
GET    /documents/{business_id}             Listar documentos
DELETE /documents/{business_id}/{doc_id}    Eliminar documento y sus chunks
```

### Calendarios

```
GET    /calendars              Listar (filtro: business_id)
GET    /calendars/{id}         Detalle con content_pieces
GET    /calendars/{id}/pieces  Solo los content pieces
PATCH  /calendars/{id}         Actualizar
```

### Contenido

```
GET    /content         Listar pieces (filtros: calendar_id, platform)
GET    /content/{id}    Detalle
PATCH  /content/{id}    Editar (caption, hashtags, fecha, status...)
```

### Suscripciones

```
GET  /subscriptions/status   Estado del plan, uso mensual y límites
```

### Administración (requiere `role=admin`)

```
GET    /admin/users                       Listar usuarios (paginado + filtros)
GET    /admin/users/{id}                  Detalle + métricas
PATCH  /admin/users/{id}/deactivate       Soft delete (conserva datos, bloquea login)
PATCH  /admin/users/{id}/reactivate       Reactivar cuenta
DELETE /admin/users/{id}                  Hard delete (irreversible, CASCADE)
GET    /admin/activity                    Log global de actividad con filtros
```

---

## Despliegue

| Capa | Plataforma | Notas |
|---|---|---|
| **Frontend** | Vercel | Auto-deploy desde `main` |
| **Backend** | Railway | Nixpacks, Python 3.12 |
| **Base de datos** | PostgreSQL 17 en Railway | `DATABASE_URL` inyectada automáticamente |

### Backend — Railway (`nixpacks.toml`)

```toml
[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

Las migraciones de Alembic se ejecutan automáticamente en cada deploy antes de arrancar el servidor.

### CORS

El backend acepta requests desde:
- `http://localhost:3000` (desarrollo)
- `https://*.vercel.app` (producción, regex)

---

## Variables de Entorno

### Backend (`backend/.env`)

```env
# Base de datos
DATABASE_URL=sqlite+aiosqlite:///./socialgenius.db
# Producción: postgresql+asyncpg://user:pass@host:5432/db

# JWT
JWT_SECRET_KEY=clave-secreta-aleatoria-larga
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# HuggingFace
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxx
HUGGINGFACE_MODEL=Qwen/Qwen2.5-72B-Instruct

# Stripe
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx
STRIPE_PRO_PRICE_ID=price_xxxxxxxxxxxxxxxxxxxx

# App
APP_NAME=SocialGenius
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Instalación Local

### Requisitos

- Python 3.12+
- Node.js 18+
- API key de HuggingFace (gratuita en huggingface.co/settings/tokens)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Configurar variables
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva disponible en `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
# Crear frontend/.env.local con NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm run dev
```

Abrir `http://localhost:3000`.

---

## Estructura del Proyecto

```
SocialGenius-AI/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── engine.py              # HuggingFace AsyncInferenceClient + streaming
│   │   │   └── prompts/               # 5 prompts especializados + general
│   │   ├── api/v1/                    # Endpoints REST (routers por dominio)
│   │   ├── models/                    # SQLAlchemy ORM models (10 tablas)
│   │   ├── schemas/                   # Pydantic schemas (request/response)
│   │   ├── services/
│   │   │   ├── chat_service.py        # Core del chat + auto-parsing de calendarios
│   │   │   ├── rag_service.py         # RAG: chunking, embeddings HF API, búsqueda coseno
│   │   │   └── admin_service.py       # Gestión de usuarios (soft/hard delete)
│   │   ├── config.py                  # Pydantic Settings (auto-deriva SYNC_DATABASE_URL)
│   │   └── main.py                    # FastAPI app + lifespan (create_all + migraciones runtime)
│   ├── alembic/                       # Migraciones versionadas
│   ├── nixpacks.toml                  # Build config para Railway
│   ├── railway.toml                   # Deploy config (startCommand, healthcheck)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── app/                       # Next.js App Router (páginas y layouts)
    │   │   └── (dashboard)/           # Route group con layout autenticado
    │   ├── components/                # Componentes reutilizables + shadcn/ui
    │   ├── hooks/                     # useChat (SSE state management)
    │   ├── lib/                       # api-client.ts (JWT + SSE), utils
    │   └── types/                     # TypeScript types globales
    └── package.json
```
