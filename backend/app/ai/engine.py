import logging
from collections.abc import AsyncGenerator

from huggingface_hub import AsyncInferenceClient

from app.config import settings

logger = logging.getLogger(__name__)
from app.core.constants import ConversationType
from app.models.business import Business

from .prompts.business_analysis import BusinessAnalysisPrompt
from .prompts.calendar_creation import CalendarCreationPrompt
from .prompts.content_strategy import ContentStrategyPrompt
from .prompts.copywriting import CopywritingPrompt
from .prompts.hashtag_research import HashtagResearchPrompt

# Prompt registry
PROMPT_REGISTRY = {
    ConversationType.BUSINESS_ANALYSIS: BusinessAnalysisPrompt,
    ConversationType.CONTENT_STRATEGY: ContentStrategyPrompt,
    ConversationType.CALENDAR_CREATION: CalendarCreationPrompt,
    ConversationType.COPYWRITING: CopywritingPrompt,
    ConversationType.HASHTAG_RESEARCH: HashtagResearchPrompt,
}

# Parámetros de generación por tipo de conversación
# CALENDAR_CREATION: temperatura baja → respeta el formato exacto del prompt
# COPYWRITING: temperatura alta → más creatividad y variedad
# BUSINESS_ANALYSIS / CONTENT_STRATEGY: equilibrio entre creatividad y rigor
GENERATION_PARAMS: dict[ConversationType, dict] = {
    ConversationType.CALENDAR_CREATION:  {"temperature": 0.35, "max_tokens": 3000},
    ConversationType.BUSINESS_ANALYSIS:  {"temperature": 0.55, "max_tokens": 3000},
    ConversationType.CONTENT_STRATEGY:   {"temperature": 0.65, "max_tokens": 3000},
    ConversationType.HASHTAG_RESEARCH:   {"temperature": 0.70, "max_tokens": 1500},
    ConversationType.COPYWRITING:        {"temperature": 0.85, "max_tokens": 1500},
    ConversationType.GENERAL:            {"temperature": 0.75, "max_tokens": 2048},
}

# General assistant system prompt
GENERAL_SYSTEM_PROMPT = """Eres SocialGenius, un asistente de IA experto en marketing digital
y redes sociales. Ayudas a emprendedores y pequeñas empresas a crear estrategias
de contenido efectivas para Instagram y TikTok. Responde de manera clara,
accionable y específica. Responde siempre en español."""


class AIEngine:
    def __init__(self):
        self._hf_client: AsyncInferenceClient | None = None

    @property
    def hf_client(self) -> AsyncInferenceClient:
        if self._hf_client is None:
            self._hf_client = AsyncInferenceClient(
                api_key=settings.HUGGINGFACE_API_KEY,
            )
        return self._hf_client

    async def stream_response(
        self,
        conversation_type: ConversationType,
        messages: list[dict],
        business: Business | None = None,
    ) -> AsyncGenerator[str | dict, None]:
        # Build system prompt
        prompt_class = PROMPT_REGISTRY.get(conversation_type)
        if prompt_class:
            system_prompt = prompt_class.build(business=business)
        else:
            system_prompt = GENERAL_SYSTEM_PROMPT

        params = GENERATION_PARAMS.get(conversation_type, GENERATION_PARAMS[ConversationType.GENERAL])
        model = settings.HUGGINGFACE_MODEL
        yield {"model": model}

        async for chunk in self._stream_huggingface(system_prompt, messages, model, params):
            yield chunk

    async def _stream_huggingface(
        self, system_prompt: str, messages: list[dict], model: str, params: dict
    ) -> AsyncGenerator[str, None]:
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(messages)

        logger.debug(
            "Prompt enviado al modelo | model=%s temp=%.2f max_tokens=%d msgs=%d "
            "system_chars=%d",
            model, params["temperature"], params["max_tokens"],
            len(api_messages), len(system_prompt),
        )

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

ai_engine = AIEngine()
