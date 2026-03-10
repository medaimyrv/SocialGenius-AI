"""Tests unitarios para el parser de calendarios de la IA."""
from datetime import date

import pytest

from app.services.chat_service import (
    _extract_field,
    _parse_calendar_blocks,
    _split_into_post_blocks,
)
from app.core.constants import ContentFormat

WEEK_START = date(2026, 3, 16)  # Lunes


# ---------------------------------------------------------------------------
# _extract_field
# ---------------------------------------------------------------------------

def test_extract_field_plain():
    block = "TEMA: Beneficios del pan artesanal\nHORA: 10:00"
    assert _extract_field(block, "TEMA") == "Beneficios del pan artesanal"


def test_extract_field_bold_markdown():
    block = "**TEMA**: Recetas de verano\n**HORA**: 09:00"
    assert _extract_field(block, "TEMA") == "Recetas de verano"


def test_extract_field_italic_markdown():
    block = "*TEMA*: Ideas creativas\n*HORA*: 11:00"
    assert _extract_field(block, "TEMA") == "Ideas creativas"


def test_extract_field_missing_returns_none():
    block = "HORA: 10:00\nCAPTION: Texto"
    assert _extract_field(block, "TEMA") is None


def test_extract_field_with_bullet():
    block = "- **CAPTION**: Descubre nuestros panes\n- **HASHTAGS**: #pan"
    assert _extract_field(block, "CAPTION") == "Descubre nuestros panes"


# ---------------------------------------------------------------------------
# _split_into_post_blocks
# ---------------------------------------------------------------------------

def test_split_by_separator():
    text = "Lunes | Instagram\nTEMA: Pan\n---\nJueves | TikTok\nTEMA: Café"
    blocks = _split_into_post_blocks(text)
    assert len(blocks) == 2


def test_split_multiple_days_no_separator():
    text = "Lunes | Instagram\nTEMA: Pan\nJueves | TikTok\nTEMA: Café"
    blocks = _split_into_post_blocks(text)
    assert len(blocks) >= 2


def test_split_single_post():
    text = "Lunes | Instagram\nTEMA: Pan\nHORA: 10:00"
    blocks = _split_into_post_blocks(text)
    assert len(blocks) == 1


# ---------------------------------------------------------------------------
# _parse_calendar_blocks — formato estándar
# ---------------------------------------------------------------------------

STANDARD_RESPONSE = """
Lunes | Instagram | Reel
HORA: 09:00
TEMA: Beneficios del pan artesanal
GANCHO: ¿Sabías que el pan de masa madre tiene más nutrientes?
CAPTION: Descubre por qué nuestro pan es diferente. Elaborado con amor cada mañana.
HASHTAGS: #panartesanal #masaMadre #panaderia
VISUAL: Panadero sacando pan del horno
CTA: Visítanos en el local

---

Jueves | Instagram | Carrusel
HORA: 18:00
TEMA: Proceso de elaboración del pan
GANCHO: Así se hace el mejor pan de la ciudad
CAPTION: Desde el amasado hasta el horneado, te mostramos cada paso.
HASHTAGS: #proceso #artesanal #panaderia
VISUAL: Serie de fotos del proceso
CTA: Guarda este post para compartirlo
"""


def test_parse_returns_two_pieces():
    pieces = _parse_calendar_blocks(STANDARD_RESPONSE, WEEK_START)
    assert len(pieces) == 2


def test_parse_lunes_date():
    pieces = _parse_calendar_blocks(STANDARD_RESPONSE, WEEK_START)
    lunes = next(p for p in pieces if p["day_of_week"] == "Lunes")
    assert lunes["scheduled_date"] == date(2026, 3, 16)


def test_parse_jueves_date():
    pieces = _parse_calendar_blocks(STANDARD_RESPONSE, WEEK_START)
    jueves = next(p for p in pieces if p["day_of_week"] == "Jueves")
    assert jueves["scheduled_date"] == date(2026, 3, 19)


def test_parse_platform_instagram():
    pieces = _parse_calendar_blocks(STANDARD_RESPONSE, WEEK_START)
    assert all(p["platform"] == "instagram" for p in pieces)


def test_parse_content_format_reel():
    pieces = _parse_calendar_blocks(STANDARD_RESPONSE, WEEK_START)
    lunes = next(p for p in pieces if p["day_of_week"] == "Lunes")
    assert lunes["content_format"] == ContentFormat.REEL


def test_parse_content_format_carousel():
    pieces = _parse_calendar_blocks(STANDARD_RESPONSE, WEEK_START)
    jueves = next(p for p in pieces if p["day_of_week"] == "Jueves")
    assert jueves["content_format"] == ContentFormat.CAROUSEL


def test_parse_scheduled_time():
    pieces = _parse_calendar_blocks(STANDARD_RESPONSE, WEEK_START)
    lunes = next(p for p in pieces if p["day_of_week"] == "Lunes")
    assert lunes["scheduled_time"] is not None
    assert lunes["scheduled_time"].hour == 9


def test_parse_hashtags_list():
    pieces = _parse_calendar_blocks(STANDARD_RESPONSE, WEEK_START)
    lunes = next(p for p in pieces if p["day_of_week"] == "Lunes")
    assert "#panartesanal" in lunes["hashtags"]
    assert "#masaMadre" in lunes["hashtags"]


def test_parse_topic_and_caption():
    pieces = _parse_calendar_blocks(STANDARD_RESPONSE, WEEK_START)
    lunes = next(p for p in pieces if p["day_of_week"] == "Lunes")
    assert "pan artesanal" in lunes["topic"].lower()
    assert "diferente" in lunes["caption"].lower()


# ---------------------------------------------------------------------------
# Casos edge: formato con asteriscos (salida de Qwen/Mistral)
# ---------------------------------------------------------------------------

BOLD_FORMAT_RESPONSE = """
**Lunes** | Instagram | Reel

**TEMA**: Tips para emprendedores
**HORA**: 10:00
**GANCHO**: ¿Quieres crecer en redes?
**CAPTION**: Hoy te compartimos 3 tips esenciales para tu negocio.
**HASHTAGS**: #emprendedor #tips #negocio
**VISUAL**: Persona trabajando en laptop
**CTA**: Síguenos para más contenido

---

**Miércoles** | TikTok | Video

**TEMA**: Detrás de cámaras
**HORA**: 19:00
**GANCHO**: Así es un día en nuestra empresa
**CAPTION**: Te mostramos cómo trabajamos cada día.
**HASHTAGS**: #detrasdelcamara #empresa
**VISUAL**: Video del equipo trabajando
**CTA**: Comenta qué quieres ver
"""


def test_parse_bold_format_two_pieces():
    pieces = _parse_calendar_blocks(BOLD_FORMAT_RESPONSE, WEEK_START)
    assert len(pieces) == 2


def test_parse_bold_format_days():
    pieces = _parse_calendar_blocks(BOLD_FORMAT_RESPONSE, WEEK_START)
    days = {p["day_of_week"] for p in pieces}
    assert "Lunes" in days
    assert "Miércoles" in days


def test_parse_bold_format_tiktok_platform():
    pieces = _parse_calendar_blocks(BOLD_FORMAT_RESPONSE, WEEK_START)
    miercoles = next(p for p in pieces if p["day_of_week"] == "Miércoles")
    assert miercoles["platform"] == "tiktok"


# ---------------------------------------------------------------------------
# Casos edge: sin separadores
# ---------------------------------------------------------------------------

NO_SEPARATOR_RESPONSE = """
Lunes | Instagram | Story
TEMA: Oferta del día
CAPTION: ¡Solo hoy! 2x1 en pasteles.
HASHTAGS: #oferta #pastel

Viernes | Instagram | Reel
TEMA: Receta del fin de semana
CAPTION: Esta receta te va a encantar.
HASHTAGS: #receta #findeSemana
"""


def test_parse_no_separator_finds_both_posts():
    pieces = _parse_calendar_blocks(NO_SEPARATOR_RESPONSE, WEEK_START)
    assert len(pieces) >= 2
    days = {p["day_of_week"] for p in pieces}
    assert "Lunes" in days
    assert "Viernes" in days


# ---------------------------------------------------------------------------
# Casos edge: respuesta vacía o sin posts
# ---------------------------------------------------------------------------

def test_parse_empty_response():
    pieces = _parse_calendar_blocks("", WEEK_START)
    assert pieces == []


def test_parse_response_without_days():
    pieces = _parse_calendar_blocks("Aquí hay texto pero sin días de la semana.", WEEK_START)
    assert pieces == []
