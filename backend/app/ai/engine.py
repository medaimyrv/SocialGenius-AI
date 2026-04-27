"""
AI Engine — Capa de abstracción sobre HuggingFace Inference API.

Responsabilidades:
  1. Elegir el system prompt correcto según el tipo de conversación
  2. Ajustar los parámetros de generación (temperatura, tokens) por tipo
  3. Hacer streaming de tokens del modelo al caller
  4. Reintentar automáticamente si el modelo está cargando (503)

Modelo usado: Qwen2.5-72B-Instruct (via HuggingFace Inference API)
  - Contexto de 128K tokens — no hay riesgo de overflow con MAX_HISTORY=20
  - Compatible con el formato de mensajes OpenAI (role/content)
  - Responde en español por instrucción en el system prompt

Por qué streaming:
  El usuario ve tokens apareciendo en tiempo real en lugar de esperar 10-30s
  a que el modelo genere toda la respuesta. Usamos SSE (Server-Sent Events)
  para enviar cada token al frontend según llega de la API.

Por qué retry con backoff:
  HuggingFace carga los modelos on-demand. Si el modelo no está caliente
  devuelve 503 con "Model is currently loading". Reintentar 1-2 veces
  con espera exponencial resuelve el 95% de estos casos sin necesitar
  un endpoint de "warm-up" dedicado.
"""
import asyncio
import logging
from collections.abc import AsyncGenerator

from huggingface_hub import AsyncInferenceClient

from app.config import settings
from app.core.constants import ConversationType
from app.models.business import Business

from .prompts.business_analysis import BusinessAnalysisPrompt
from .prompts.calendar_creation import CalendarCreationPrompt
from .prompts.content_strategy import ContentStrategyPrompt
from .prompts.copywriting import CopywritingPrompt
from .prompts.hashtag_research import HashtagResearchPrompt

logger = logging.getLogger(__name__)

# ── Registro de prompts ───────────────────────────────────────────────────────
# Mapea tipo de conversación → clase de prompt.
# Cada clase tiene un método .build(business) que devuelve el system prompt
# con el contexto del negocio ya interpolado.
PROMPT_REGISTRY = {
    ConversationType.BUSINESS_ANALYSIS: BusinessAnalysisPrompt,
    ConversationType.CONTENT_STRATEGY: ContentStrategyPrompt,
    ConversationType.CALENDAR_CREATION: CalendarCreationPrompt,
    ConversationType.COPYWRITING: CopywritingPrompt,
    ConversationType.HASHTAG_RESEARCH: HashtagResearchPrompt,
}

# ── Parámetros de generación por tipo ────────────────────────────────────────
# La temperatura controla la aleatoriedad del modelo:
#   0.0 → completamente determinista (mismo input → mismo output siempre)
#   1.0 → máxima creatividad (respuestas muy variadas)
#
# Principio: cuanto más estructurado debe ser el output, menor temperatura.
#   - CALENDAR_CREATION: 0.35 — necesitamos el bloque --- exacto que parsea el backend
#   - COPYWRITING:       0.85 — creatividad alta para textos de marketing variados
#   - El resto:          equilibrio entre rigor y originalidad
GENERATION_PARAMS: dict[ConversationType, dict] = {
    ConversationType.CALENDAR_CREATION:  {"temperature": 0.35, "max_tokens": 3000},
    ConversationType.BUSINESS_ANALYSIS:  {"temperature": 0.55, "max_tokens": 3000},
    ConversationType.CONTENT_STRATEGY:   {"temperature": 0.65, "max_tokens": 3000},
    ConversationType.HASHTAG_RESEARCH:   {"temperature": 0.70, "max_tokens": 1500},
    ConversationType.COPYWRITING:        {"temperature": 0.85, "max_tokens": 1500},
    ConversationType.GENERAL:            {"temperature": 0.75, "max_tokens": 2048},
}

# Prompt base para conversaciones generales (sin tipo especializado)
GENERAL_SYSTEM_PROMPT = (
    "Eres SocialGenius, un asistente de IA experto en marketing digital "
    "y redes sociales. Ayudas a emprendedores y pequeñas empresas a crear estrategias "
    "de contenido efectivas para Instagram y TikTok. Responde de manera clara, "
    "accionable y específica. Responde siempre en español."
)


class AIEngine:
    """
    Singleton que gestiona la conexión con HuggingFace y orquesta la generación.

    Inicialización lazy del cliente: no conecta hasta el primer request.
    Esto permite importar el módulo sin que falle si la API key no está
    configurada (útil en tests o scripts de migración).
    """

    def __init__(self):
        self._hf_client: AsyncInferenceClient | None = None

    @property
    def hf_client(self) -> AsyncInferenceClient:
        """Inicializa el cliente HuggingFace en el primer uso."""
        if self._hf_client is None:
            self._hf_client = AsyncInferenceClient(api_key=settings.HUGGINGFACE_API_KEY)
        return self._hf_client

    async def stream_response(
        self,
        conversation_type: ConversationType,
        messages: list[dict],
        business: Business | None = None,
    ) -> AsyncGenerator[str | dict, None]:
        """
        Punto de entrada principal: construye el prompt y hace streaming de la respuesta.

        Yields:
          - Un dict {"model": "<model_id>"} como primer item (metadata para el cliente)
          - Strings de texto con los tokens generados (uno por chunk de la API)

        El primer yield con metadata permite al frontend mostrar qué modelo se está
        usando sin necesidad de un endpoint separado de configuración.
        """
        prompt_class = PROMPT_REGISTRY.get(conversation_type)
        system_prompt = prompt_class.build(business=business) if prompt_class else GENERAL_SYSTEM_PROMPT
        params = GENERATION_PARAMS.get(conversation_type, GENERATION_PARAMS[ConversationType.GENERAL])
        model = settings.HUGGINGFACE_MODEL

        # Enviamos el modelo como primer token para que el cliente pueda mostrarlo
        yield {"model": model}

        async for token in self._stream_huggingface(system_prompt, messages, model, params):
            yield token

    async def _stream_huggingface(
        self,
        system_prompt: str,
        messages: list[dict],
        model: str,
        params: dict,
    ) -> AsyncGenerator[str, None]:
        """
        Llama a la API de HuggingFace con reintentos automáticos.

        Estrategia de retry:
          - Intento 1: inmediato
          - Intento 2: espera 1s (el modelo puede estar cargando)
          - Intento 3: espera 2s
          - Si falla el intento 3: propaga la excepción al caller

        El caller (send_message_and_stream en chat_service.py) captura la excepción
        y la convierte en un evento SSE de error para que el frontend la muestre.
        """
        api_messages = [{"role": "system", "content": system_prompt}, *messages]

        logger.debug(
            "HF request | model=%s temp=%.2f max_tokens=%d msgs=%d system_chars=%d",
            model, params["temperature"], params["max_tokens"],
            len(api_messages), len(system_prompt),
        )

        last_error = None
        for attempt in range(3):
            try:
                stream = await self.hf_client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    stream=True,
                    temperature=params["temperature"],
                    max_tokens=params["max_tokens"],
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return  # éxito — salir del loop de reintentos

            except Exception as e:
                last_error = e
                if attempt < 2:
                    wait = 2 ** attempt  # 1s, 2s
                    logger.warning(
                        "HuggingFace API error (intento %d/3): %s — reintentando en %ds",
                        attempt + 1, e, wait,
                    )
                    await asyncio.sleep(wait)

        raise last_error


# Instancia global — reutilizamos el cliente HTTP entre requests (connection pooling)
ai_engine = AIEngine()
