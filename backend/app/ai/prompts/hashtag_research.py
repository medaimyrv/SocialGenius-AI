from app.models.business import Business


class HashtagResearchPrompt:
    @classmethod
    def build(cls, business: Business | None) -> str:
        business_context = cls._format_business(business) if business else ""

        return f"""Eres SocialGenius, un experto en hashtags y tendencias para Instagram y TikTok.

Datos del negocio:
{business_context}

Cuando el usuario pida hashtags, responde con estas secciones (usa markdown):
1. **Hashtags principales** (5-8): los mas importantes para la industria
2. **Hashtags de nicho** (5-8): mas pequenos pero con comunidades activas
3. **Hashtags de marca** (2-3): personalizados para este negocio
4. **Set listo para copiar**: un grupo de 15 hashtags combinados, listos para pegar

Reglas: Solo hashtags reales y relevantes. Mezcla populares + nicho. NO repitas. Responde en espanol."""

    @classmethod
    def _format_business(cls, business: Business) -> str:
        parts = [
            f"Nombre: {business.name}",
            f"Industria: {business.industry}",
            f"Descripcion: {business.description}",
        ]
        if business.target_audience:
            parts.append(f"Audiencia objetivo: {business.target_audience}")
        if business.instagram_handle:
            parts.append(f"Instagram: @{business.instagram_handle}")
        if business.tiktok_handle:
            parts.append(f"TikTok: @{business.tiktok_handle}")
        return "\n".join(parts)
