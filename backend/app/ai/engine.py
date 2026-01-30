from collections.abc import AsyncGenerator

import anthropic
import openai

from app.config import settings
from app.core.constants import ConversationType
from app.models.business import Business

from .prompts.business_analysis import BusinessAnalysisPrompt
from .prompts.calendar_creation import CalendarCreationPrompt
from .prompts.content_strategy import ContentStrategyPrompt
from .prompts.copywriting import CopywritingPrompt
from .prompts.hashtag_research import HashtagResearchPrompt

# Model routing: which AI model to use for each conversation type
MODEL_ROUTING = {
    ConversationType.BUSINESS_ANALYSIS: "anthropic",
    ConversationType.CONTENT_STRATEGY: "anthropic",
    ConversationType.CALENDAR_CREATION: "openai",
    ConversationType.COPYWRITING: "openai",
    ConversationType.HASHTAG_RESEARCH: "openai",
    ConversationType.GENERAL: "openai",
}

# Prompt registry
PROMPT_REGISTRY = {
    ConversationType.BUSINESS_ANALYSIS: BusinessAnalysisPrompt,
    ConversationType.CONTENT_STRATEGY: ContentStrategyPrompt,
    ConversationType.CALENDAR_CREATION: CalendarCreationPrompt,
    ConversationType.COPYWRITING: CopywritingPrompt,
    ConversationType.HASHTAG_RESEARCH: HashtagResearchPrompt,
}

# General assistant system prompt
GENERAL_SYSTEM_PROMPT = """Eres SocialGenius, un asistente de IA experto en marketing digital
y redes sociales. Ayudas a emprendedores y pequenas empresas a crear estrategias
de contenido efectivas para Instagram y TikTok. Responde de manera clara,
accionable y especifica. Responde siempre en espanol."""


class AIEngine:
    def __init__(self):
        self._openai_client: openai.AsyncOpenAI | None = None
        self._anthropic_client: anthropic.AsyncAnthropic | None = None

    @property
    def openai_client(self) -> openai.AsyncOpenAI:
        if self._openai_client is None:
            self._openai_client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY
            )
        return self._openai_client

    @property
    def anthropic_client(self) -> anthropic.AsyncAnthropic:
        if self._anthropic_client is None:
            self._anthropic_client = anthropic.AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )
        return self._anthropic_client

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

        # Select provider
        provider = MODEL_ROUTING.get(conversation_type, "openai")

        if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            async for chunk in self._stream_anthropic(system_prompt, messages):
                yield chunk
        else:
            async for chunk in self._stream_openai(system_prompt, messages):
                yield chunk

    async def _stream_openai(
        self, system_prompt: str, messages: list[dict]
    ) -> AsyncGenerator[str | dict, None]:
        model = settings.DEFAULT_OPENAI_MODEL
        yield {"model": model}

        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(messages)

        stream = await self.openai_client.chat.completions.create(
            model=model,
            messages=api_messages,
            stream=True,
            temperature=0.7,
            max_tokens=4096,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _stream_anthropic(
        self, system_prompt: str, messages: list[dict]
    ) -> AsyncGenerator[str | dict, None]:
        model = settings.DEFAULT_ANTHROPIC_MODEL
        yield {"model": model}

        # Filter out system messages from the message list for Anthropic
        api_messages = [
            msg for msg in messages if msg["role"] != "system"
        ]

        async with self.anthropic_client.messages.stream(
            model=model,
            system=system_prompt,
            messages=api_messages,
            max_tokens=4096,
            temperature=0.7,
        ) as stream:
            async for text in stream.text_stream:
                yield text
