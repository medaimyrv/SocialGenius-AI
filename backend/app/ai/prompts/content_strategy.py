from app.models.business import Business


class ContentStrategyPrompt:
    @classmethod
    def build(cls, business: Business | None) -> str:
        business_context = cls._format_business(business) if business else ""

        return f"""Eres SocialGenius, un estratega experto en contenido para Instagram y TikTok.

Datos del negocio:
{business_context}

Cuando el usuario pida una estrategia de contenido, responde con estos puntos (usa markdown):
1. Pilares de Contenido (3-5 temas recurrentes)
2. Mix de formatos por plataforma (Reels, Carruseles, Stories, Videos TikTok)
3. Frecuencia recomendada (3-5 posts/semana)
4. Horarios optimos para publicar
5. 5 ideas concretas de contenido con formato y descripcion
6. Tacticas de crecimiento organico

Reglas: Se especifico para este negocio. Solo crecimiento organico. NO repitas secciones. Responde en espanol."""

    @classmethod
    def _format_business(cls, business: Business) -> str:
        parts = [
            f"Nombre: {business.name}",
            f"Industria: {business.industry}",
            f"Descripcion: {business.description}",
        ]
        if business.target_audience:
            parts.append(f"Audiencia objetivo: {business.target_audience}")
        if business.brand_voice:
            parts.append(f"Voz de marca: {business.brand_voice}")
        if business.instagram_handle:
            parts.append(f"Instagram: @{business.instagram_handle}")
        if business.tiktok_handle:
            parts.append(f"TikTok: @{business.tiktok_handle}")
        return "\n".join(parts)
