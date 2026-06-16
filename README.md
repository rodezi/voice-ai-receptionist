# AI Voice Operations for Real Estate

An end-to-end AI voice system designed to handle inbound calls, qualify real estate prospects, recommend relevant properties, schedule appointments, register leads in a CRM, and generate structured post-call reports.

The system is designed for real estate teams that need to respond to inbound inquiries consistently, including during periods when human agents are unavailable or managing other prospects.

> **Language:** Spanish — Mexico
> **Primary use case:** Real estate lead intake and qualification
> **Location context:** Mexico City real estate market

---

## Business Problem

Real estate teams regularly receive inquiries while advisors are occupied, outside working hours, or unable to answer immediately.

This can result in:

* Missed inbound opportunities
* Inconsistent lead qualification
* Incomplete prospect information
* Delayed appointment scheduling
* Manual CRM data entry
* Limited visibility into call activity
* Leads being lost between communication channels

This project explores how voice AI can support the first stage of the real estate sales process by handling repetitive intake tasks and transferring structured information to the sales team.

---

## Solution Overview

The AI voice agent handles the initial prospect interaction and coordinates the downstream operational workflow.

It can:

* Answer inbound calls in Mexican Spanish
* Collect structured buyer or renter requirements
* Qualify prospects based on predefined criteria
* Search an approved property knowledge base
* Present relevant property options
* Schedule appointments through Cal.com
* Register prospects and call data in Airtable
* Generate structured post-call summaries using Anthropic
* Provide operational data for a monitoring dashboard

The system is intended to support human advisors, not replace them. Qualified prospects and relevant context are passed to the team for continued follow-up.

---

## System Workflow

```text
Inbound call
     ↓
Twilio phone number
     ↓
Retell AI voice agent
     ↓
Prospect qualification
     ↓
Property knowledge lookup
     ↓
Appointment booking
     ↓
Lead registration in Airtable
     ↓
Post-call report generation
     ↓
Operational dashboard
```

---

## Core Capabilities

### Inbound Call Handling

Twilio receives the call and routes it to the Retell AI voice agent.

The agent follows a controlled conversational flow and communicates exclusively in Spanish adapted to the Mexican market.

---

### Prospect Qualification

During the conversation, the agent collects relevant information such as:

* Prospect name
* Phone number
* Property type
* Preferred area or neighborhood
* Approximate budget
* Purchase, rental, or investment intent
* Level of interest
* Appointment preference

The information is converted into structured data for downstream systems.

---

### Property Search

The agent searches the property information available in its approved knowledge base.

It is instructed to:

* Only mention available properties
* Avoid inventing listings or details
* Ask clarifying questions when information is incomplete
* Explain when no matching property is currently available
* Escalate or register the request for human follow-up when needed

---

### Appointment Scheduling

When a prospect is qualified and interested, the agent can use Cal.com to:

* Check available appointment times
* Schedule a meeting or property visit
* Associate the appointment with the correct prospect
* Save the booking information in the CRM

---

### CRM Registration

Airtable acts as the source of truth for lead status.

Each record may include:

* Name
* Phone number
* Property requirements
* Preferred location
* Budget
* Purchase or rental intent
* Qualification status
* Appointment status
* Appointment date and time
* Call summary
* Follow-up status

Prospects who do not qualify are still registered with the appropriate status so the team maintains a complete interaction history.

---

### Post-Call Reporting

After each completed call, the system sends the transcript or relevant call data to the Anthropic API.

The model generates a structured report containing information such as:

* Prospect intent
* Qualification summary
* Main requirements
* Objections or concerns
* Properties discussed
* Appointment outcome
* Recommended next action

The report is then stored in the corresponding Airtable lead record.

Post-call processing is designed to run asynchronously so it does not block the main webhook response.

---

### Operational Dashboard

The planned dashboard provides visibility into the system's activity.

Potential metrics include:

* Active calls
* Total calls
* Completed calls
* Missed or failed calls
* Qualified leads
* Unqualified leads
* Appointments scheduled
* Lead conversion rate
* Provider errors
* Average call duration
* Post-call reports generated

> The dashboard module is currently planned and may not yet be included in the implemented version.

---

## Architecture

| Component              | Technology    | Responsibility                                                                  |
| ---------------------- | ------------- | ------------------------------------------------------------------------------- |
| Voice agent            | Retell AI     | Voice interaction, conversational logic, tool execution, and property knowledge |
| Telephony              | Twilio        | Phone number provisioning and inbound call routing                              |
| Backend                | Python        | Webhook processing, validation, orchestration, and business logic               |
| Scheduling             | Cal.com       | Appointment availability and booking                                            |
| CRM                    | Airtable      | Lead storage, qualification status, and follow-up data                          |
| Post-call intelligence | Anthropic API | Structured call summaries and recommended actions                               |
| Dashboard              | To be defined | Operational monitoring and reporting                                            |

---

## Project Structure

```text
ai-voice-real-estate-operations/
├── README.md
├── CLAUDE.md
├── main.py
├── pyproject.toml
├── dashboard/
│   └── ...
├── webhooks/
│   ├── retell_webhook.py
│   ├── twilio_webhook.py
│   └── calcom_webhook.py
├── integrations/
│   ├── airtable_client.py
│   ├── calcom_client.py
│   └── anthropic_client.py
├── utils/
│   └── ...
├── examples/
│   ├── sample_call_payload.json
│   ├── sample_lead_record.json
│   └── sample_post_call_report.json
└── docs/
    ├── architecture/
    └── screenshots/
```

---

## Technical Design Principles

The project follows these implementation principles:

* Python 3.11 or later
* Dependency management with `uv`
* Webhook signature validation before processing
* Asynchronous post-call report generation
* Separation between integration clients and business logic
* Airtable as the primary lead record
* Retell AI as the source of the voice-agent prompt and conversation configuration
* Environment variables for secrets and provider credentials
* Explicit handling of third-party failures
* Structured logging for webhook and integration activity
* Duplicate-event prevention where supported
* Graceful fallback when a provider is temporarily unavailable

---

## Reliability Considerations

A production implementation should account for the following scenarios:

* Duplicate webhook events
* Invalid webhook signatures
* Missing or incomplete call data
* Anthropic API timeouts
* Airtable API failures
* Cal.com booking conflicts
* Property lookup failures
* Interrupted calls
* Invalid prospect information
* Provider rate limits
* Partial workflow completion

Potential reliability mechanisms include:

* Idempotency keys
* Retry policies
* Exponential backoff
* Request timeouts
* Structured error responses
* Failure notifications
* Dead-letter or retry queues
* Correlation IDs
* Manual review states

---

## Environment Variables

Create a `.env` file using the following structure:

```env
# Retell AI
RETELL_API_KEY=

# Twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Cal.com
CALCOM_API_KEY=
CALCOM_EVENT_TYPE_ID=

# Airtable
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=
AIRTABLE_TABLE_LEADS=

# Anthropic
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=
```

Never commit real credentials or production secrets to the repository.

---

## Example Lead Record

```json
{
  "name": "Example Prospect",
  "phone": "+52XXXXXXXXXX",
  "property_type": "Apartment",
  "preferred_location": "Condesa",
  "budget_mxn": 6500000,
  "intent": "Purchase",
  "qualification_status": "Qualified",
  "appointment_scheduled": true,
  "appointment_datetime": "2026-06-20T11:00:00-06:00",
  "call_summary": "Prospect is looking for a two-bedroom apartment and is available for a visit this week.",
  "recommended_next_action": "Confirm the appointment and send matching listings."
}
```

---

## Agent Behavior

The voice agent follows several operational restrictions:

* Communicates only in Spanish adapted to Mexico
* Maintains a professional, helpful, and direct tone
* Does not invent property listings
* Only presents information available in the approved knowledge base
* Requests clarification when prospect information is incomplete
* Registers both qualified and unqualified prospects
* Closes conversations politely
* Escalates cases that require human judgment
* Avoids making legal, financial, or contractual commitments
* Clearly indicates when information must be confirmed by a human advisor

---

## My Role

I designed and implemented the system architecture and integration workflow, including:

* Voice AI use-case definition
* Conversation and qualification flow design
* Retell AI agent configuration
* Twilio call routing
* Webhook architecture
* Airtable CRM data structure
* Cal.com appointment workflow
* Anthropic post-call reporting
* Integration logic
* Failure-handling strategy
* Project documentation

---

## Project Status

This repository documents the architecture, integration design, and selected implementation components of the system.

Some third-party configurations, credentials, private prompts, production data, and customer-specific information are intentionally excluded.

Current status:

* [x] Voice-agent use case defined
* [x] Qualification flow designed
* [x] Retell AI agent configured
* [x] Twilio inbound calling configured
* [x] Airtable CRM structure defined
* [x] Cal.com appointment flow designed
* [x] Anthropic post-call reporting designed
* [ ] Production monitoring dashboard
* [ ] Expanded automated testing
* [ ] Production-grade queue and retry infrastructure
* [ ] Advanced analytics and reporting

Update the checklist above so it accurately reflects the implementation currently available in the repository.

---

## Demo

Add your demo links here:

* **Voice agent demo:** [Watch demo](YOUR_DEMO_URL)
* **Architecture walkthrough:** [Watch walkthrough](YOUR_LOOM_URL)
* **Live phone demo:** Available upon request

---

## Screenshots

Suggested screenshots:

1. Retell AI agent configuration
2. Example inbound call
3. Airtable lead record
4. Cal.com appointment
5. Structured Anthropic report
6. Workflow or backend logs

Store images inside:

```text
docs/screenshots/
```

Then reference them from this README:

```markdown
![Airtable lead record](docs/screenshots/airtable-lead-record.png)
```

---

## Limitations

The current project has several known limitations:

* Property information depends on the quality and freshness of the configured knowledge base
* Voice AI responses may require further testing across accents, noise levels, and unusual requests
* Airtable may not be appropriate as the long-term database for high-volume production usage
* Third-party provider availability affects the complete workflow
* Human review remains necessary for sensitive or ambiguous cases
* The dashboard and advanced monitoring layer are still under development

---

## Potential Improvements

Future iterations may include:

* PostgreSQL as the primary operational database
* Redis for temporary state and deduplication
* Background workers for post-call tasks
* Centralized logs and distributed tracing
* Real-time operations dashboard
* Automatic advisor assignment
* WhatsApp follow-up after each call
* Property database synchronization
* Multi-office support
* Role-based access control
* Conversation analytics
* Cost and latency monitoring
* Automated testing of conversation paths
* Human transfer during live calls

---

## Use Case Disclaimer

This project is intended as a technical implementation and portfolio case study.

It does not guarantee lead conversion, revenue growth, appointment attendance, or replacement of human real estate advisors. Business outcomes depend on lead volume, property availability, operational processes, follow-up quality, and market conditions.

---

## Contact

**Rodrigo Zayas**
AI Integrations Specialist

* GitHub: [github.com/rodezi](https://github.com/rodezi)
* LinkedIn: [Add LinkedIn profile](www.linkedin.com/in/rodrigo-zayas-e)
* Email: [rodezayas@gmail.com](mailto:rodezayas@gmail.com)
* Location: Querétaro, Mexico
