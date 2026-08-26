# The Lenny Growth Assistant

An AI-powered conversational workspace and RAG assistant grounded strictly in transcripts from **Lenny's Podcast**. Built using FastAPI, PostgreSQL + pgvector, Nginx, and local LLM orchestration (Ollama).

---

## Core Features

*   **Cyber-Minimalist Console UI:** Dark high-contrast obsidian slate workspace layout.
*   **Persistent Conversations:** Session histories, message logging, and metadata preservation in PostgreSQL.
*   **Grounded RAG Pipeline:** Vector search via `pgvector` with a $\ge 0.4$ cosine similarity threshold. A fallback protection blocks general knowledge hallucinations if no relevant transcript context is retrieved.
*   **Unified LLM Router:** Dropdown toggle supporting Local Ollama (`qwen2.5-coder:7b` chat + `nomic-embed-text` embeddings), OpenAI, and Anthropic.
*   **Ship 30 for 30 Essay Builder:** Custom agent router that compiles retrieved podcast frameworks into an actionable ~1200-word structured Markdown essay.
*   **Sandboxed Artifact Viewer:** Side-by-side interactive drawer that renders HTML/CSS elements securely using `iframe` isolation.

---

## Technical Architecture

For details regarding database schema layouts, component boundaries, and security parameters, see the **[Architecture Specification](architecture.md)** and the **[Design Specification](design.md)**.

---

## Prerequisites

Before starting, ensure you have the following installed on your host machine:

1.  **Docker & Docker Compose** (Docker Desktop on Windows/Mac/Linux).
2.  **Ollama (Local)**.
3.  **Required Ollama Models:**
    ```bash
    ollama pull nomic-embed-text
    ollama pull qwen2.5-coder:7b
    ```

---

## Quick Start (Dockerized Production Run)

Getting the entire ecosystem running requires only one command.

### 1. Configure the Environment
Copy the example environment file:
```bash
cp .env.example .env
```
*(If you want to use cloud providers, edit `.env` and add your `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. Otherwise, leave it as is to run completely free and local).*

### 2. Startup Containers
Spin up the DB, API, and Web frontend containers:
```bash
docker-compose up --build -d
```
Docker Compose will launch:
*   **Frontend Web App:** `http://localhost:8080` (Console UI)
*   **FastAPI Backend API:** `http://localhost:8000` (docs at `http://localhost:8000/docs`)
*   **Postgres DB (pgvector):** Exposed internally to containers and on host port `5435`

---

## Database Ingestion

To populate your database with transcript vector chunks:

1.  **Create local Virtual Env:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate      # Windows Powershell
    pip install -r backend/requirements.txt
    ```
2.  **Execute Ingest Script:**
    Ensure Ollama is running on your host, then run:
    ```bash
    python backend/scripts/ingest.py
    ```
    This script chunks the transcripts from the curated growth/PMF episodes index and embeds them into Postgres.

---

## Running Automated Tests

A Python test suite is included to verify sessions, REST API contracts, and vector search fallback logic:

```bash
cd backend
..\venv\Scripts\python -m unittest tests/test_backend.py
```

---

## Troubleshooting

### Error: `WinError 10013 (Access permissions / Socket already in use)`
*   *Cause:* Port `8000` or `5435` is already being used on your host machine.
*   *Fix:* Check if you have a local instance of uvicorn running in a shell and terminate it (`Ctrl + C`), or check if another postgres container is bound to those ports.

### Error: `Read timed out (timeout=180)` during first Ollama query
*   *Cause:* Ollama is performing a "cold start" to load the 4.7 GB model from disk to memory.
*   *Fix:* The backend timeout has been extended to 180s to wait safely. Try executing the query again; subsequent requests are hot in memory and process in under 5 seconds.
