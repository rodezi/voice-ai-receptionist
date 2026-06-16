"""
Retell AI webhook — handles call lifecycle events.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, BackgroundTasks, Header, Request, Response

from dashboard.state import emit_event
from integrations import airtable_client
from integrations.anthropic_client import generate_call_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["retell"])

# Module-level mapping: call_id → Airtable record_id
_call_records: dict[str, str] = {}

# Thread pool for running sync Anthropic calls without blocking the event loop
_executor = ThreadPoolExecutor(max_workers=4)


# ---------------------------------------------------------------------------
# Signature validation
# ---------------------------------------------------------------------------


def _validate_retell_signature(body: bytes, signature: str) -> bool:
    """Validate the HMAC-SHA256 signature sent by Retell AI."""
    from utils.config import RETELL_API_KEY

    try:
        expected = base64.b64encode(
            hmac.new(RETELL_API_KEY.encode(), body, hashlib.sha256).digest()
        ).decode()
        return hmac.compare_digest(expected, signature)
    except Exception as exc:
        logger.error("Error computing Retell signature: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Background task: generate report and update Airtable
# ---------------------------------------------------------------------------


def _generate_and_save_report(
    record_id: str,
    transcript: str,
    call_data: dict,
) -> None:
    """Blocking function: generate report and persist it to Airtable."""
    try:
        report_text = generate_call_report(transcript, call_data)
        airtable_client.update_lead(record_id, {"Reporte": report_text})
        emit_event(
            "report_generated",
            {
                "call_id": call_data.get("call_id"),
                "record_id": record_id,
                "nombre": call_data.get("nombre"),
            },
        )
        logger.info(
            "Reporte guardado en Airtable. record_id=%s call_id=%s",
            record_id,
            call_data.get("call_id"),
        )
    except Exception as exc:
        logger.error("Error generando/guardando reporte: %s", exc)


# ---------------------------------------------------------------------------
# POST /webhook/retell
# ---------------------------------------------------------------------------


@router.post("/retell")
async def retell_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_retell_signature: str = Header(default="", alias="x-retell-signature"),
) -> Response:
    """Handle Retell AI lifecycle events."""

    raw_body = await request.body()

    # --- Signature validation ---
    if not _validate_retell_signature(raw_body, x_retell_signature):
        logger.warning("Invalid Retell signature. Rejecting request.")
        return Response(content='{"error":"forbidden"}', status_code=403, media_type="application/json")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        logger.error("Could not parse Retell webhook body: %s", exc)
        return Response(content='{"error":"bad_request"}', status_code=400, media_type="application/json")

    event: str = payload.get("event", "")
    call: dict = payload.get("call", {})
    call_id: str = call.get("call_id", "")

    logger.info("Retell event received: %s call_id=%s", event, call_id)

    # ── call_started ──────────────────────────────────────────────────────
    if event == "call_started":
        from_number: str = call.get("from_number", "")
        to_number: str = call.get("to_number", "")

        emit_event(
            "call_started",
            {
                "call_id": call_id,
                "from_number": from_number,
                "to_number": to_number,
                "timestamp": call.get("start_timestamp"),
            },
        )

    # ── call_ended ────────────────────────────────────────────────────────
    elif event == "call_ended":
        from_number = call.get("from_number", "")
        to_number = call.get("to_number", "")
        transcript: str = call.get("transcript", "")
        duration_ms: int = call.get("end_timestamp", 0) - call.get("start_timestamp", 0)
        duration_seconds: int = max(0, duration_ms // 1000)

        # Extract structured analysis produced by Retell's post-call analysis
        call_analysis: dict = call.get("call_analysis", {})
        custom_data: dict = call_analysis.get("custom_analysis_data", {}) if call_analysis else {}

        nombre: str = custom_data.get("nombre") or from_number
        zona: str = custom_data.get("zona", "")
        tipo_propiedad: str = custom_data.get("tipo_propiedad", "")
        presupuesto: str = str(custom_data.get("presupuesto", ""))
        cita_agendada: bool = bool(custom_data.get("cita_agendada", False))
        calificado: bool = bool(custom_data.get("calificado", True))

        estatus = "Calificado" if calificado else "No calificado"

        airtable_fields = {
            "Nombre": nombre,
            "Telefono": from_number,
            "Tipo de propiedad": [tipo_propiedad] if tipo_propiedad else [],
            "Zona de Interés": zona,
            "Presupuesto": presupuesto,
            "Cita_Agendada": cita_agendada,
            "Resumen_Llamada": transcript[:5000] if transcript else "",
            "Estado del Lead": [estatus] if estatus else [],
            "call_id": call_id,
            "Duracion_Segundos": duration_seconds,
        }

        try:
            record_id = airtable_client.create_lead(airtable_fields)
            _call_records[call_id] = record_id
            logger.info("Lead registrado. call_id=%s record_id=%s", call_id, record_id)
        except Exception as exc:
            logger.error("Error registrando lead en Airtable: %s", exc)
            record_id = ""

        emit_event(
            "call_ended",
            {
                "call_id": call_id,
                "from_number": from_number,
                "nombre": nombre,
                "estatus": estatus,
                "duracion_segundos": duration_seconds,
                "cita_agendada": cita_agendada,
                "record_id": record_id,
            },
        )

    # ── call_analyzed ─────────────────────────────────────────────────────
    elif event == "call_analyzed":
        record_id = _call_records.get(call_id, "")

        if not record_id:
            logger.warning("call_analyzed: no Airtable record found for call_id=%s", call_id)
            return Response(content='{"status":"ok"}', media_type="application/json")

        transcript = call.get("transcript", "")
        call_analysis = call.get("call_analysis", {})
        custom_data = call_analysis.get("custom_analysis_data", {}) if call_analysis else {}

        call_data_for_report = {
            "call_id": call_id,
            "nombre": custom_data.get("nombre") or call.get("from_number", ""),
            "telefono": call.get("from_number", ""),
            "tipo_propiedad": custom_data.get("tipo_propiedad", ""),
            "zona": custom_data.get("zona", ""),
            "presupuesto": str(custom_data.get("presupuesto", "")),
            "duracion_segundos": max(
                0,
                (call.get("end_timestamp", 0) - call.get("start_timestamp", 0)) // 1000,
            ),
            "cita_agendada": bool(custom_data.get("cita_agendada", False)),
        }

        # Run the blocking Anthropic call in background (non-blocking)
        background_tasks.add_task(
            _generate_and_save_report,
            record_id,
            transcript,
            call_data_for_report,
        )

    else:
        logger.debug("Unhandled Retell event: %s", event)

    return Response(content='{"status":"ok"}', media_type="application/json")
