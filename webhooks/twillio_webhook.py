"""
Twilio webhook — receives inbound calls and registers them with Retell AI.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Form, Header, Request, Response
from twilio.request_validator import RequestValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["twilio"])

RETELL_REGISTER_URL = "https://api.retellai.com/v2/register-phone-call"


# ---------------------------------------------------------------------------
# POST /webhook/twilio
# ---------------------------------------------------------------------------


@router.post("/twilio")
async def twilio_webhook(
    request: Request,
    From: str = Form(default=""),
    To: str = Form(default=""),
    x_twilio_signature: str = Header(default="", alias="x-twilio-signature"),
) -> Response:
    """
    Handle inbound Twilio calls:
    1. Validate Twilio request signature.
    2. Register the call with Retell AI.
    3. Return TwiML to bridge the call via WebSocket.
    """
    from utils.config import (
        PUBLIC_URL,
        RETELL_AGENT_ID,
        RETELL_API_KEY,
        TWILIO_AUTH_TOKEN,
        TWILIO_PHONE_NUMBER,
    )

    # --- Twilio signature validation ---
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    form_data = await request.form()
    params = dict(form_data)

    # Behind Railway's proxy the internal URL differs from the public one Twilio
    # signed against.  Use PUBLIC_URL when set so validation succeeds.
    if PUBLIC_URL:
        from urllib.parse import urlparse
        parsed = urlparse(str(request.url))
        base = PUBLIC_URL.rstrip("/")
        url = base + parsed.path
        if parsed.query:
            url += "?" + parsed.query
    else:
        url = str(request.url)

    if not validator.validate(url, params, x_twilio_signature):
        logger.warning("Invalid Twilio signature from %s. Rejecting.", request.client.host if request.client else "unknown")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Reject/></Response>',
            status_code=403,
            media_type="application/xml",
        )

    from_number: str = From or params.get("From", "")
    to_number: str = To or params.get("To", TWILIO_PHONE_NUMBER)

    logger.info("Inbound Twilio call from=%s to=%s", from_number, to_number)

    # --- Register call with Retell AI ---
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            retell_response = await client.post(
                RETELL_REGISTER_URL,
                headers={
                    "Authorization": f"Bearer {RETELL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "agent_id": RETELL_AGENT_ID,
                    "from_number": from_number,
                    "to_number": to_number,
                },
            )
            retell_response.raise_for_status()
            retell_data: dict = retell_response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Retell AI registration failed: status=%s body=%s",
            exc.response.status_code,
            exc.response.text,
        )
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say language="es-MX">Lo sentimos, ocurrió un error. Por favor intente más tarde.</Say></Response>',
            status_code=200,
            media_type="application/xml",
        )
    except Exception as exc:
        logger.error("Error registering call with Retell AI: %s", exc)
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say language="es-MX">Lo sentimos, ocurrió un error. Por favor intente más tarde.</Say></Response>',
            status_code=200,
            media_type="application/xml",
        )

    call_id: str = retell_data.get("call_id", "")
    access_token: str = retell_data.get("access_token", "")

    logger.info("Retell call registered. call_id=%s", call_id)

    # --- Return TwiML to connect the call ---
    # v2 API no devuelve access_token; solo incluir el Parameter si existe.
    if access_token:
        stream_params = f'\n      <Parameter name="access_token" value="{access_token}"/>'
    else:
        stream_params = ""

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://api.retellai.com/audio-websocket/{call_id}">{stream_params}
    </Stream>
  </Connect>
</Response>"""

    return Response(content=twiml, status_code=200, media_type="application/xml")
