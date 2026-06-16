"""
Airtable CRM client — manages lead records for the voice AI agent.
"""

from __future__ import annotations

import logging
from typing import Any

from pyairtable import Api

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy initialisation — avoids import-time env-var errors during testing
# ---------------------------------------------------------------------------

_table: Any = None  # pyairtable.Table


def _get_table() -> Any:
    global _table
    if _table is None:
        from utils.config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_LEADS

        _table = Api(AIRTABLE_API_KEY).table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_LEADS)
    return _table


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_lead(fields: dict) -> str:
    """Create a new lead record in Airtable and return the record ID."""
    table = _get_table()
    try:
        record = table.create(fields)
        record_id: str = record["id"]
        logger.info("Lead created in Airtable. record_id=%s", record_id)
        return record_id
    except Exception as exc:
        logger.error("Error creating lead in Airtable: %s", exc)
        raise


def update_lead(record_id: str, fields: dict) -> None:
    """Update an existing lead record in Airtable."""
    table = _get_table()
    try:
        table.update(record_id, fields)
        logger.info("Lead updated in Airtable. record_id=%s", record_id)
    except Exception as exc:
        logger.error("Error updating lead in Airtable record_id=%s: %s", record_id, exc)
        raise


def get_lead_by_call_id(call_id: str) -> dict | None:
    """Search for a lead by call_id field. Returns the first match or None."""
    table = _get_table()
    try:
        formula = f"{{call_id}}='{call_id}'"
        records = table.all(formula=formula)
        if records:
            return records[0]
        return None
    except Exception as exc:
        logger.error("Error searching lead by call_id=%s: %s", call_id, exc)
        raise


def get_lead_by_phone(phone: str) -> dict | None:
    """Search for a lead by phone number. Returns the first match or None."""
    table = _get_table()
    try:
        formula = f"{{Telefono}}='{phone}'"
        records = table.all(formula=formula)
        if records:
            return records[0]
        return None
    except Exception as exc:
        logger.error("Error searching lead by phone=%s: %s", phone, exc)
        raise
