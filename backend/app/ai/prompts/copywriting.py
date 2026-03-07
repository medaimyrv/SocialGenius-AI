from app.models.business import Business


class CopywritingPrompt:
    @classmethod
    def build(cls, business: Business | None) -> str:
        business_context = cls._format_business(business) if business else ""

        return f"""Eres SocialGenius, un copywriter experto en redes sociales para Instagram y TikTok.

Datos del negocio:
{business_context}

Cuando el usuario pida copy, genera 2 opciones (Opcion A y Opcion B) con este formato:

## Opcion A
**Gancho:** primera linea que detiene el scroll
**Caption:** texto completo listo para publicar
**CTA:** llamada a la accion
**Por que funciona:** una linea de justificacion

Reglas: Instagram = 150-300 caracteres, pulido. TikTok = menos de 150 caracteres, conversacional. Usa emojis con moderacion. NO repitas contenido entre opciones. Responde en espanol."""

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
        return "\n".join(parts)
