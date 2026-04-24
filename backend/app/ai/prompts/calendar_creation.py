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

EJEMPLO REAL (sigue este modelo exacto):

---
POST: Lunes | Instagram | Reel
HORA: 18:00
TEMA: 3 errores que cometen los emprendedores al publicar en Instagram
GANCHO: Si publicas todos los dias y no creces, probablemente estes cometiendo este error
CAPTION: Llevas meses publicando y los seguidores no llegan? El problema no es la frecuencia, es la estrategia. Aqui los 3 errores mas comunes y como corregirlos hoy mismo.
HASHTAGS: #emprendimiento #instagramtips #marketingdigital #redessociales #crecimientopersonal
VISUAL: Persona frente a telefono con expresion de frustracion, fondo neutro, texto animado con los 3 errores en pantalla
CTA: Guarda este video y comparte con ese amigo que lo necesita
---
---
POST: Miercoles | TikTok | Video
HORA: 19:30
TEMA: Como duplicar ventas sin gastar en publicidad
GANCHO: Esto lo hacen las marcas grandes y casi nadie en tu nicho lo usa
CAPTION: La estrategia de contenido que usan las marcas millonarias adaptada para negocios pequenos. Sin presupuesto de publicidad.
HASHTAGS: #ventas #estrategiadigital #tiktokbusiness #emprendedores #marketing
VISUAL: Persona hablando a camara con graficos simples apareciendo en pantalla, iluminacion natural
CTA: Sigueme para mas estrategias gratuitas cada semana
---

REGLAS OBLIGATORIAS:
- Usa EXACTAMENTE los campos POST/HORA/TEMA/GANCHO/CAPTION/HASHTAGS/VISUAL/CTA en ese orden
- Los dias validos son: Lunes, Martes, Miercoles, Jueves, Viernes, Sabado, Domingo
- Las plataformas son: Instagram o TikTok (2 de cada una)
- Los formatos validos son: Reel, Carrusel, Imagen, Story, Video, Live
- Captions reales y completos listos para publicar, personalizados para el negocio
- Hashtags reales y relevantes al negocio y al tema
- NO escribas introducciones, titulos ni explicaciones antes o despues
- Empieza directamente con --- y termina con ---
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
