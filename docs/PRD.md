# Discovery Brief & Product Requirements: The Lenny Growth Assistant

**Prepared by:** Swarnika Somvanshi(Forward Deployed Engineer applicant)
**Project:** The Lenny Growth Assistant

---

## 1. User & Problem

*   **My Target User:** Internal Product Management and Growth team members at Oogway Labs.
*   **The Job to Complete:** Quickly find, synthesize, and format actionable growth strategies, mental models, and product management frameworks from Lenny’s Podcast transcripts, and produce reusable written content based on these insights.
*   **The Pain I am Removing:** Right now, extracting specific frameworks or advice requires listening to hours of audio or manually searching and reading through lengthy text transcripts. This assistant eliminates that manual effort by instantly providing grounded answers and generating highly formatted content (like the Ship 30 for 30 essays) based on trusted sources, without requiring you to engineer complex prompts or manage LLM infrastructure.

---

## 2. Success Metrics

*   **Operational Success Metric (Time-to-Content):** A reduction in the time it takes a growth team member to draft a strategy document or essay based on Lenny's frameworks (e.g., reducing draft time from hours to minutes).
*   **Product Success Metric (Trust & Engagement):** 
    *   Citations that link directly to the source episode via `youtube_url`, alongside guest and title.
    *   How often users successfully render and copy generated Markdown or HTML/CSS artifacts for their internal use.

---

## 3. My Assumptions

Because the initial brief was open-ended, I made the following key assumptions to guide my implementation:
*   **Knowledge Base Format:** I am using the public transcript repository which contains 269 episodes. To keep ingestion, embedding generation times, and evaluation runtimes reasonable for this take-home review, I decided to ingest a representative subset of 23 growth-focused and PMF-focused episodes (using the repository's own index) rather than indexing the entire archive.
*   **Deployment Setup:** I assume you (the evaluator) prefer a completely containerized environment (`docker-compose`) that sets up the database (PostgreSQL + `pgvector`), backend API, and static frontend server seamlessly with a single command.
*   **Model Selection:** I assume local LLM usage (via Ollama) is preferred for privacy, offline development, and zero API costs, but that the architecture should let you easily switch to cloud models (like OpenAI or Claude) if you need higher reasoning quality.
*   **Ship 30 for 30 Skill:** I assume this requires enforcing a strict structural template (hook, narrative, formatting, specific takeaway) programmatically via the agent layer, rather than relying on the user to prompt for it correctly.
*   **Hallucination Prevention:** If semantic retrieval doesn't find any transcript chunks above a similarity threshold (set to `0.4`), the assistant should state it has no grounded information rather than answering from general LLM knowledge.

---

## 4. Scope Choices

### What I Included:
*   **RAG Pipeline with pgvector:** Ingesting the curated subset of transcripts, chunked and indexed semantically to ensure all assistant answers are strictly grounded in Lenny's actual data.
*   **Flexible Agent Routing & LLM Toggle:** A backend router that supports standard chat vs. essay generation, and a dropdown configuration to swap between local Ollama and cloud providers dynamically.
*   **Secure Artifact Viewer:** A dedicated split-panel UI that uses a sandboxed `iframe` to render generated Markdown and HTML/CSS elements securely.
*   **Ship 30 for 30 Essay Generator:** A specialized agent route that translates raw transcript facts into a ~1,200-word highly structured essay.

### What I Intentionally Excluded:
*   **User Authentication (OAuth/SSO):** I left this out to keep setup and evaluation friction as low as possible for you. The focus is strictly on the AI, database, and agent architecture.
*   **Audio Processing / Real-time Transcription:** Excluded because the knowledge source is explicitly defined as the existing transcript archive.
*   **Complex Multi-Agent Chains:** I favored a clean, robust router (Standard Chat vs. Essay Skill) to ensure low latency and maintainability.

---

## 5. Risks & Trade-offs

*   **Hallucination vs. Creativity:** To prevent hallucinations, I designed the system prompt to strictly force the LLM to use only the retrieved context. The trade-off is that the assistant might refuse to answer perfectly valid product questions if they aren't explicitly covered in the ingested transcripts.
*   **Local Model Latency:** Running Ollama locally ensures privacy and zero API costs, but trade-offs include higher latency depending on the host machine's hardware. I addressed this by raising the backend connection timeout to 180 seconds.
*   **Untrusted Artifact Rendering:** Generating HTML/CSS poses XSS risks. To mitigate this, my Artifact Viewer implements strict `iframe` sandboxing (`sandbox="allow-scripts"` without `allow-same-origin`), prioritizing parent session security.

---

## 6. User Flows

Here is the operational path I implemented:
1.  **Session Initialization:** The user opens the console UI at `http://localhost:8080` and clicks `NEW TERMINAL` to initialize a session in Postgres.
2.  **Toggle Settings:** The user selects the preferred model provider and switches between "Standard RAG" and "Ship 30 for 30" modes.
3.  **Prompt Submission:** The user submits a growth query. The UI locks input and shows a status indicator.
4.  **Semantic Search:** 
    *   The backend retrieves the top 5 chunks.
    *   If similarity is $\ge 0.4$, the assistant generates a response using the context.
    *   If similarity is low, the pipeline bypasses LLM call and returns a static grounded denial message immediately.
5.  **Rendering:** Chat bubble displays markdown rendering and source citation links. Generating HTML/Markdown automatically opens the sandboxed split-screen preview panel.

---

## 7. Technical Implementation Details

I built the application using the following stack:
*   **PostgreSQL + pgvector:** Database schema mapping vector dimensions to `768` (for `nomic-embed-text`) with unique constraints on chunk indexes to prevent duplicate ingestion.
*   **FastAPI Backend:** Lightweight Python API containing Pydantic settings loading, Unified LLM wrappers (using direct `requests` calls for lightweight execution), and SQLAlchemy database session management.
*   **Web Console:** Minimalist dark slate panel interface built with Vanilla HTML/CSS/JS, incorporating a markdown parser library and sandboxed iframe containers.

---

## 8. Acceptance Criteria

*   **RAG Groundedness:** On test queries covering the ingested episode subset, ≥90% of answers cite a real, correctly-attributed episode (guest, title, and youtube_url match).
*   **Essay Skill Accuracy:** The Ship 30 for 30 essay generator produces output between 1,200–1,250 words, with a clear hook, subheaders, bold text, and one explicit takeaway, in ≥4 out of 5 runs.
*   **Setup Reliability:** A fresh `git clone` + `docker-compose up` results in a fully running system (DB, backend, frontend) with zero manual intervention beyond copying `.env`.
*   **Security Isolation:** Raw HTML code rendered in the preview frame cannot access the parent page's local storage or DOM objects.