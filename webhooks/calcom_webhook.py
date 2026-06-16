"""
Cal.com webhook — handles booking lifecycle events.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dashboard.state import emit_event
from integrations import airtable_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["calcom"])


# ---------------------------------------------------------------------------
# POST /webhook/calcom
# ---------------------------------------------------------------------------


@router.post("/calcom")
async def calcom_webhook(request: Request) -> JSONResponse:
    """
    Handle Cal.com booking events.
    - BOOKING_CREATED: update the matching Airtable lead with appointment details.
    - Other events are acknowledged but not processed.
    """
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error("Could not parse Cal.com webhook body: %s", exc)
        return JSONResponse(content={"status": "error", "detail": "invalid_json"}, status_code=400)

    trigger_event: str = payload.get("triggerEvent", "")
    logger.info("Cal.com event received: %s", trigger_event)

    if trigger_event == "BOOKING_CREATED":
        booking: dict = payload.get("payload", {})

        # Extract attendee data (Cal.com v2 format)
        attendees: list = booking.get("attendees", [])
        attendee: dict = attendees[0] if attendees else {}

        nombre: str = attendee.get("name", "") or booking.get("title", "")
        email: str = attendee.get("email", "")
        phone: str = attendee.get("phone", "") or _extract_phone_from_responses(booking)
        start_time: str = booking.get("startTime", "")
        end_time: str = booking.get("endTime", "")
        booking_uid: str = booking.get("uid", "")

        logger.info(
            "BOOKING_CREATED: nombre=%s email=%s phone=%s start=%s uid=%s",
            nombre,
            email,
            phone,
            start_time,
            booking_uid,
        )

        # Try to find the matching lead in Airtable by phone number
        if phone:
            try:
                lead = airtable_client.get_lead_by_phone(phone)
                if lead:
                    record_id: str = lead["id"]
                    airtable_client.update_lead(
                        record_id,
                        {
                            "Cita_Agendada": True,
                            "Fecha_Cita": start_time,
                            "Cal_Booking_ID": booking_uid,
                        },
                    )
                    logger.info(
                        "Lead actualizado con cita. record_id=%s booking_uid=%s",
                        record_id,
                        booking_uid,
                    )
                else:
                    logger.warning(
                        "No se encontró lead con teléfono=%s para actualizar cita.", phone
                    )
            except Exception as exc:
                logger.error("Error actualizando lead en Airtable para cita: %s", exc)

        emit_event(
            "appointment_scheduled",
            {
                "nombre": nombre,
                "email": email,
                "phone": phone,
                "startTime": start_time,
                "endTime": end_time,
                "booking_uid": booking_uid,
            },
        )

    elif trigger_event == "BOOKING_CANCELLED":
        booking = payload.get("payload", {})
        booking_uid = booking.get("uid", "")
        logger.info("BOOKING_CANCELLED: uid=%s", booking_uid)
        # Future: update Airtable to reflect cancellation

    elif trigger_event == "BOOKING_RESCHEDULED":
        booking = payload.get("payload", {})
        booking_uid = booking.get("uid", "")
        new_start = booking.get("startTime", "")
        logger.info("BOOKING_RESCHEDULED: uid=%s new_start=%s", booking_uid, new_start)
        # Future: update Airtable with new date

    else:
        logger.debug("Unhandled Cal.com event: %s", trigger_event)

    return JSONResponse(content={"status": "ok"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_phone_from_responses(booking: dict) -> str:
    """Try to extract phone number from booking responses field."""
    responses = booking.get("responses", {})
    if isinstance(responses, dict):
        phone = responses.get("phone", "")
        if phone:
            return str(phone)
    return ""
