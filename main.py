"""
AI Voice Operations — Entry point.
Agente de voz IA para inmobiliaria CDMX.
"""

from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from webhooks.retell_webhook import router as retell_router
from webhooks.twilio_webhook import router as twilio_router
from webhooks.calcom_webhook import router as calcom_router
from dashboard.router import router as dashboard_router

app = FastAPI(
    title="AI Voice Operations",
    description="Agente de voz IA para inmobiliaria CDMX",
    version="0.1.0",
)

app.include_router(retell_router)
app.include_router(twilio_router)
app.include_router(calcom_router)
app.include_router(dashboard_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Voice Operations"}
