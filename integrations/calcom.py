"""
Cal.com client — handles slot availability queries and booking creation.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

CALCOM_API_BASE = "https://api.cal.com/v2"


def get_available_slots(start_time: str, end_time: str) -> dict:
    """
    Fetch available booking slots from Cal.com.

    Parameters
    ----------
    start_time : str
        ISO 8601 datetime string for range start (e.g. "2024-06-01T00:00:00Z").
    end_time : str
        ISO 8601 datetime string for range end.

    Returns
    -------
    dict
        Response JSON from the Cal.com API containing available slots.
    """
    from utils.config import CALCOM_API_KEY, CALCOM_EVENT_TYPE_ID

    params = {
        "apiKey": CALCOM_API_KEY,
        "eventTypeId": CALCOM_EVENT_TYPE_ID,
        "startTime": start_time,
        "endTime": end_time,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(f"{CALCOM_API_BASE}/slots", params=params)
            response.raise_for_status()
            data: dict = response.json()
            logger.info("Slots obtenidos de Cal.com para rango %s - %s", start_time, end_time)
            return data
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Error HTTP obteniendo slots de Cal.com: status=%s body=%s",
            exc.response.status_code,
            exc.response.text,
        )
        raise
    except Exception as exc:
        logger.error("Error obteniendo slots de Cal.com: %s", exc)
        raise


def create_booking(
    nombre: str,
    email: str,
    telefono: str,
    start: str,
    notes: str = "",
) -> dict:
    """
    Create a new booking in Cal.com.

    Parameters
    ----------
    nombre : str
        Attendee's full name.
    email : str
        Attendee's email address.
    telefono : str
        Attendee's phone number.
    start : str
        ISO 8601 datetime string for the booking start time.
    notes : str
        Optional notes / observations about the booking.

    Returns
    -------
    dict
        Response JSON from the Cal.com API with the created booking details.
    """
    from utils.config import CALCOM_API_KEY, CALCOM_EVENT_TYPE_ID

    payload = {
        "eventTypeId": int(CALCOM_EVENT_TYPE_ID),
        "start": start,
        "responses": {
            "name": nombre,
            "email": email,
            "phone": telefono,
        },
        "timeZone": "America/Mexico_City",
        "language": "es",
        "metadata": {
            "notas": notes,
        },
    }

    params = {"apiKey": CALCOM_API_KEY}

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                f"{CALCOM_API_BASE}/bookings",
                params=params,
                json=payload,
            )
            response.raise_for_status()
            data: dict = response.json()
            logger.info(
                "Cita creada en Cal.com. uid=%s nombre=%s start=%s",
                data.get("uid"),
                nombre,
                start,
            )
            return data
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Error HTTP creando cita en Cal.com: status=%s body=%s",
            exc.response.status_code,
            exc.response.text,
        )
        raise
    except Exception as exc:
        logger.error("Error creando cita en Cal.com: %s", exc)
        raise
