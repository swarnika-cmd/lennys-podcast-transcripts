# Forward Deployment Brief (PRD): The Lenny Growth Assistant

**Prepared for:** Oogway Labs Evaluators
**Project:** The Lenny Growth Assistant

---

## 1. User and Problem
**Primary User:** Internal Product Management and Growth team members at Oogway Labs.
**Job to Complete:** The users need to quickly find, synthesize, and format actionable growth strategies, mental models, and product management frameworks from Lenny’s Podcast transcripts. They also need to produce reusable written content based on these insights.
**Pain Removed:** Currently, extracting specific frameworks or advice requires listening to hours of audio or manually searching and reading through lengthy text transcripts. The assistant eliminates this manual effort by instantly providing grounded answers and generating highly formatted content (like the Ship 30 for 30 essays) based on trusted sources, without requiring the user to engineer complex prompts or manage LLM infrastructure.

## 2. Success Metric
**Operational Success Metric:** 
- **Time-to-Content:** A reduction in the time it takes a growth team member to draft a strategy document or essay based on Lenny's frameworks (e.g., reducing draft time from hours to minutes).

**Product Success Metric:**
- **Citation Click-Through Rate & Trust:** Citations will link directly to the source episode via youtube_url, alongside guest and title from frontmatter.
- **Artifact Utilization:** The number of generated artifacts (HTML/Markdown) that are successfully rendered and copied for internal use without hallucinated claims.

## 3. Assumptions
Due to the open-ended nature of the initial brief, the following assumptions were made:
- **Knowledge Base Format:** Using the public transcripts archive: 269 episode transcripts, each stored as episodes/{guest-name}/transcript.md with YAML frontmatter (guest, title, youtube_url, video_id, publish_date, duration) followed by the full transcript body. Given the take-home scope, ingestion will target a representative subset of 23 growth-focused and PMF-focused episodes rather than the full 269, to keep ingestion/embedding time and evaluation runtime reasonable.
- **Deployment Environment:** Assumed the Oogway Labs evaluator prefers a completely containerized setup (Docker Compose) that handles the database (PostgreSQL + pgvector), backend, and frontend static servers seamlessly.
- **Local vs. Cloud Usage:** Assumed that the local LLM (Ollama) requirement is primarily for privacy, cost-control, or offline development, whereas cloud models (Claude/OpenAI) might be preferred for complex reasoning tasks in a production setting.
- **Ship 30 for 30 Skill:** Assumed this skill requires enforcing a strict structural template (hook, narrative, formatting, specific takeaway) programmatically via the agent layer, rather than relying on the user to prompt for it correctly.
- If retrieval returns no chunks above a similarity threshold, the assistant states it has no grounded information on the topic rather than answering from general knowledge.

## 4. Scope Choices
**What is Included:**
- **RAG Pipeline with pgvector:** Ingesting a curated subset of the 269-episode ChatPRD archive, selected via the repo's pre-built topic index for Growth/PM relevance to ensure all answers are strictly grounded in the transcript data.
- **Agentic Routing & LLM Toggle:** A flexible backend that allows toggling between Local (Ollama) and Cloud (Anthropic Claude/OpenAI) models dynamically, demonstrating operational flexibility.
- **Secure Artifact Viewer:** A dedicated, side-by-side UI panel using a sandboxed `iframe` to render generated Markdown and HTML/CSS artifacts securely.
- **Ship 30 for 30 Content Skill:** A specialized agent route that formats retrieved context into a ~1,250-word structured essay.

**What is Intentionally Excluded:**
- **User Authentication (OAuth/SSO):** Excluded to reduce setup friction for the Oogway Labs evaluators. The focus is on the AI application logic and agent architecture.
- **Audio Processing / Real-time Transcription:** Excluded because the knowledge source is explicitly defined as the existing transcript repository.
- **Complex Multi-Agent Workflows:** Excluded in favor of a simpler, robust router (Standard Chat vs. Essay Skill) to ensure reliability, low latency, and ease of maintenance for a small forward-deployment engagement.

## 5. Risks and Trade-offs
- **Hallucination vs. Creativity:** To prevent hallucinations, the system prompt strictly forces the LLM to use only the retrieved context. The trade-off is that the assistant might refuse to answer perfectly valid product questions if they aren't explicitly covered in the ingested transcripts.
- **Local Model Latency & Quality:** Running Ollama locally ensures privacy and zero API costs, but trade-offs include higher latency and potentially lower reasoning quality compared to Claude 3.5 Sonnet or GPT-4o, depending on the evaluator's local hardware.
- **Untrusted Artifact Rendering:** Generating HTML/CSS poses XSS risks. To mitigate this, the Artifact Viewer implements strict `iframe` sandboxing (`sandbox="allow-scripts"` without `allow-same-origin`), prioritizing security over the ability to run complex cross-origin scripts inside the generated artifacts.
- **Data licensing:** transcripts are sourced from a community-maintained archive intended for educational/research use; this is appropriate for an internal take-home evaluation but would need a licensing review before any external/production use.

## 6. User Flows

The user journey follows a clean operational loop:
1.  **Session Initialization:** User accesses the console on port `8080` and clicks `NEW TERMINAL` in the sidebar, which makes a `POST /sessions` API request.
2.  **Input Configuration:** User selects the target LLM provider (Ollama / OpenAI / Anthropic) and Mode (Standard RAG / Ship 30 for 30) from the header/sidebar selectors.
3.  **Prompt Submission:** User enters a growth question. The UI displays an active loading state.
4.  **Semantic Retrieval & Fallback:** 
    *   FastAPI backend retrieves 5 similar chunks using cosine similarity from Postgres.
    *   *Match:* If chunks exceed the similarity threshold ($\ge 0.4$), the assistant synthesizes the grounded prompt.
    *   *No Match:* If similarity scores are low, the pipeline terminates and displays the standard fallback denial message instantly.
5.  **Citations & Rendering:** The UI displays the response bubble.
    *   Citations are rendered as clickable Youtube metadata links.
    *   Code blocks (HTML or Markdown) trigger the `Render HTML` button which slides out the sandboxed iframe viewer panel.

## 7. Technical Implementation Plan

The architecture spans the following layers:
*   **Database (PostgreSQL + pgvector):** Schema defines vector dimensions at `768` (for nomic-embed-text) and unique constraint rules on video chunks.
*   **Backend (FastAPI):**
    *   `config.py`: Environment loader with port/database fallbacks.
    *   `llm.py`: Direct API client wrapper for Ollama, OpenAI, and Anthropic.
    *   `agent.py`: Context-building prompt layer and conversational memory logger.
*   **Frontend (Nginx + HTML/CSS/JS):** A dark high-contrast console. Integrates Markdown rendering libraries and isolates HTML previews in a sandboxed container.

## 8. Acceptance Criteria & Definition of Done
- **RAG Groundedness:** On a fixed set of 5–10 test questions covering the ingested episode subset, ≥90% of answers cite a real, correctly-attributed episode (guest, title, and youtube_url match an actual ingested chunk).
- **Essay Skill Accuracy:** The Ship 30 for 30 essay generator produces output between 1,200–1,250 words, with a clear hook and one explicit takeaway, in ≥4 out of 5 test runs.
- **Setup Reliability:** A fresh `git clone` + `docker-compose up` results in a fully running system (DB, backend, frontend) with zero manual intervention beyond populating `.env`.
- **Security Sandboxing:** Generated HTML files rendered in the viewer cannot access the parent page's DOM or cookie storage (verified via Chrome DevTools console testing).