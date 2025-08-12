# BI Toba – Self-Service Analytics Chatbot Development Guide

BI Toba is our self-service analytics chatbot, inspired by the grandeur and depth of Lake Toba—the largest lake in Indonesia and one of the deepest in the world. Just like the lake’s vast, rich ecosystem, BI Toba is designed to hold a wealth of organizational data and make it easily accessible to anyone who needs insights.

The goal of BI Toba is to empower users to dive into their data without relying on technical teams for every query. It acts as a calm, vast “lake” where data flows in from various sources, and users can explore its depths through natural language queries.

By drawing from Lake Toba’s symbolism:
	•	Depth – Like Toba’s deep waters, BI Toba offers detailed, granular insights.
	•	Breadth – Just as the lake spans a vast area, BI Toba covers a wide range of data domains.
	•	Clarity – The lake’s still surface mirrors the chatbot’s clean, intuitive responses.

---

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   Chatbot API   │    │  PostgreSQL DB  │
│   (Nginx/HTML)  │◄──►│   (FastAPI)     │◄──►│   (On-Premise)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   LLM Service   │
                       │  (OpenAI/LLM)   │
                       └─────────────────┘
```

- **Web Interface**: Modern chat UI (HTML/JS, TailwindCSS, Nginx)
- **API Backend**: FastAPI app for chat, query, and export endpoints
- **Database**: Connects to your on-premise PostgreSQL BI database
- **LLM Integration**: Uses OpenAI (or compatible) for NL-to-SQL
- **Redis**: Caching, rate limiting, and session management

---

## Directory Structure

```
bi_selfservice/
  ├── api/                # FastAPI backend code
  │   ├── core/           # Config, DB, security
  │   ├── routers/        # API endpoints (chat, auth, health, export)
  │   ├── services/       # LLM and query validation logic
  │   └── utils/          # Caching, logging, rate limiting
  ├── web/                # Web UI (HTML, JS, CSS)
  ├── nginx/              # Nginx config for web and API proxy
  ├── docs/               # Documentation
  ├── Dockerfile.api      # Backend Dockerfile
  ├── Dockerfile.web      # Web UI Dockerfile
  ├── docker-compose.yml  # Multi-service deployment
  ├── requirements.txt    # Python dependencies
  ├── deploy.sh           # Deployment helper script
  └── config.env.example  # Example environment config
```

---

## Setup & Development Workflow

### 1. **Clone and Configure**
```bash
cd bi_selfservice
cp config.env.example .env
# Edit .env with your DB credentials and OpenAI API key
```

### 2. **Build and Run (Docker Compose)**
```bash
./deploy.sh
```
- Web UI: [http://localhost:8080](http://localhost:8080)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. **Key Files to Edit**
- **Backend**: `api/routers/chat.py`, `api/services/llm_service.py`, `api/core/database.py`
- **Web UI**: `web/index.html`, `web/js/app.js`
- **Config**: `.env`, `nginx/nginx.conf`, `docker-compose.yml`

### 4. **Development Tips**
- Use `DEBUG=true` in `.env` for verbose logging and auto-reload
- Hot-reload for FastAPI: `uvicorn api.main:app --reload`
- Web UI is static (edit HTML/JS, then refresh browser)
- Use `docker-compose logs -f` to view logs
- Test API endpoints with `/docs` (Swagger UI)
- For LLM, you can swap OpenAI with other providers by editing `llm_service.py`

### 5. **Security & Best Practices**
- Use read-only DB users for the chatbot
- Change all default secrets before production
- Set up SSL/TLS for Nginx in production
- Monitor logs and rate limits for abuse

---

## Example Queries for Testing
- "Show me user leads for last month"
- "Top 10 projects by leads"
- "Compare leads between different marketing channels"
- "How many listings were created in Jakarta this week?"

---

## Contributing
- Follow PEP8 for Python code
- Use clear commit messages
- Document new endpoints and features in this `docs/` folder
- Open issues/PRs for major changes

---

For questions, contact the BI Engineering team or check the main `README.md` for more details. 