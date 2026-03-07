from app.models.business import Business


class CalendarCreationPrompt:
    @classmethod
    def build(cls, business: Business | None) -> str:
        business_context = cls._format_business(business) if business else ""

        return f"""Eres SocialGenius, planificador de contenido para Instagram y TikTok.

Negocio:
{business_context}

Genera EXACTAMENTE 4 publicaciones (2 Instagram + 2 TikTok) separadas por ---

USA ESTE FORMATO EXACTO para cada publicacion, sin cambiar los nombres de los campos:

---
POST: Lunes | Instagram | Reel
HORA: 18:00
TEMA: el tema de la publicacion
GANCHO: primera frase o primeros 3 segundos del video
CAPTION: el texto completo listo para copiar y pegar
HASHTAGS: #tag1 #tag2 #tag3 #tag4 #tag5
VISUAL: descripcion de la imagen o video a crear
CTA: llamada a la accion
---

REGLAS OBLIGATORIAS:
- Usa EXACTAMENTE el formato POST/HORA/TEMA/GANCHO/CAPTION/HASHTAGS/VISUAL/CTA
- Los dias validos son: Lunes, Martes, Miercoles, Jueves, Viernes, Sabado, Domingo
- Las plataformas son: Instagram o TikTok
- Los formatos validos son: Reel, Carrusel, Imagen, Story, Video, Live
- Captions reales y completos listos para publicar
- Hashtags reales y relevantes
- NO escribas introducciones ni explicaciones, empieza directamente con el primer ---
- Responde en espanol"""

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
