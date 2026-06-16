"""
Anthropic client — generates structured post-call reports using Claude.
"""

from __future__ import annotations

import logging

import anthropic

logger = logging.getLogger(__name__)


def generate_call_report(transcript: str, call_data: dict) -> str:
    """
    Generate a structured post-call report in Spanish using Claude.

    Parameters
    ----------
    transcript : str
        Full call transcript.
    call_data : dict
        Metadata extracted from the call. Expected keys:
        nombre, telefono, tipo_propiedad, zona, presupuesto,
        duracion_segundos, cita_agendada.

    Returns
    -------
    str
        The generated report text.
    """
    from utils.config import ANTHROPIC_API_KEY

    nombre = call_data.get("nombre", "Desconocido")
    telefono = call_data.get("telefono", "N/D")
    tipo_propiedad = call_data.get("tipo_propiedad", "N/D")
    zona = call_data.get("zona", "N/D")
    presupuesto = call_data.get("presupuesto", "N/D")
    duracion_segundos = call_data.get("duracion_segundos", 0)
    cita_agendada = call_data.get("cita_agendada", False)

    cita_texto = "Sí" if cita_agendada else "No"
    duracion_texto = f"{duracion_segundos} segundos ({duracion_segundos // 60} min {duracion_segundos % 60} seg)"

    prompt = f"""Eres un asistente especializado en análisis de llamadas inmobiliarias en Ciudad de México.

A continuación se proporciona la información de una llamada y su transcripción. Genera un reporte estructurado y detallado en español.

## DATOS DE LA LLAMADA

- **Nombre del prospecto:** {nombre}
- **Teléfono:** {telefono}
- **Tipo de propiedad buscada:** {tipo_propiedad}
- **Zona de interés:** {zona}
- **Presupuesto aproximado:** {presupuesto}
- **Duración de la llamada:** {duracion_texto}
- **Cita agendada:** {cita_texto}

## TRANSCRIPCIÓN DE LA LLAMADA

{transcript}

---

Genera un reporte completo con las siguientes secciones exactas:

**RESUMEN EJECUTIVO**
Un párrafo conciso describiendo el resultado de la llamada, el perfil del prospecto y el siguiente paso acordado.

**PERFIL DEL PROSPECTO**
Análisis detallado del prospecto basado en la conversación: necesidades específicas, urgencia de búsqueda, capacidad económica estimada, preferencias observadas.

**NIVEL DE INTERÉS**
Calificación del nivel de interés del prospecto (Alto / Medio / Bajo) con justificación basada en la conversación.

**PROPIEDADES DISCUTIDAS**
Lista de propiedades o tipos de propiedades que se mencionaron o discutieron durante la llamada, incluyendo la reacción del prospecto ante cada una.

**PRÓXIMOS PASOS**
Acciones concretas recomendadas para el equipo de ventas, incluyendo fecha de seguimiento si aplica y cita agendada si corresponde.

**OBSERVACIONES ADICIONALES**
Cualquier información relevante que no encaje en las secciones anteriores: objeciones expresadas, competencia mencionada, referencias, contexto personal relevante, etc.
"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        report_text: str = message.content[0].text
        logger.info("Reporte generado exitosamente para prospecto: %s", nombre)
        return report_text
    except Exception as exc:
        logger.error("Error generando reporte con Anthropic: %s", exc)
        raise
