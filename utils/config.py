"""
Configuration module — loads all environment variables required by the project.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Required variables — raise KeyError if missing
# ---------------------------------------------------------------------------

def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise KeyError(
            f"Required environment variable '{name}' is not set. "
            "Please add it to your .env file."
        )
    return value


RETELL_API_KEY: str = _require("RETELL_API_KEY")

TWILIO_ACCOUNT_SID: str = _require("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN: str = _require("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER: str = _require("TWILIO_PHONE_NUMBER")

CALCOM_API_KEY: str = _require("CALCOM_API_KEY")
CALCOM_EVENT_TYPE_ID: str = _require("CALCOM_EVENT_TYPE_ID")

AIRTABLE_API_KEY: str = _require("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID: str = _require("AIRTABLE_BASE_ID")

ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")

RETELL_AGENT_ID: str = _require("RETELL_AGENT_ID")

# ---------------------------------------------------------------------------
# Optional variables with defaults
# ---------------------------------------------------------------------------

AIRTABLE_TABLE_LEADS: str = os.environ.get("AIRTABLE_TABLE_LEADS", "Leads")

# Public base URL of this service (e.g. https://your-app.railway.app).
# Required in production so Twilio signature validation uses the correct URL.
PUBLIC_URL: str = os.environ.get("PUBLIC_URL", "")
