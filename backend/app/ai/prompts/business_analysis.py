from app.models.business import Business


class BusinessAnalysisPrompt:
    @classmethod
    def build(cls, business: Business | None) -> str:
        business_context = cls._format_business(business) if business else "No se ha proporcionado un perfil de negocio aun."

        return f"""Eres SocialGenius, un analista de negocios experto en redes sociales (Instagram y TikTok).

Datos del negocio:
{business_context}

Cuando el usuario pida un analisis, responde con estos puntos (usa markdown):
1. Panorama de la industria y competidores en redes sociales
2. Audiencia objetivo (demografia y comportamiento online)
3. Propuestas de valor unicas para destacar en contenido
4. Pilares de contenido (3-5 temas recurrentes)
5. Oportunidades por plataforma (Instagram vs TikTok)
6. Voz de marca recomendada

Reglas: Se especifico para este negocio. Solo contenido organico. Si falta informacion, pregunta antes. NO repitas secciones. Responde en espanol."""

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
        if business.website_url:
            parts.append(f"Sitio web: {business.website_url}")
        if business.instagram_handle:
            parts.append(f"Instagram: @{business.instagram_handle}")
        if business.tiktok_handle:
            parts.append(f"TikTok: @{business.tiktok_handle}")
        return "\n".join(parts)
