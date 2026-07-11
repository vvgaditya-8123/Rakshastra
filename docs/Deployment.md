# Rakshastra Deployment Guide

Rakshastra can be deployed locally, containerized via Docker, or on-premise in air-gapped secure corporate networks.

## 1. Local Development Deployment

1. Set up virtual environment and install backend:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```
2. Set API key env vars in `.env`:
   ```bash
   GEMINI_API_KEY="your-gemini-key"
   ```
3. Run FastAPI backend server:
   ```bash
   python rakshastra_cli/web_server.py
   ```
4. Run React frontend dashboard:
   ```bash
   cd web
   npm install
   npm run dev
   ```

---

## 2. Docker Deployment

Deploy the entire stack with Docker Compose:

```bash
docker-compose up -d --build
```

This starts:
- The FastAPI backend server.
- The web dashboard container.
- Persistent volumes mapping SQLite data folders.

---

## 3. On-Premise / Air-Gapped Setup

To run Rakshastra in highly secure offline environments:
- Leverage the **Heuristic-Backed Fallback Engine** to run without active LLM internet connections.
- Package local models using Ollama and configure them in `config/gemini.yaml` using custom base URLs.
