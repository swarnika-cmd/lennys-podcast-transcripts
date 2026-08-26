# System Architecture Specification

This document details the database schema, component boundaries, ingestion/retrieval pipeline, agent routing logic, and deployment topology of **The Lenny Growth Assistant**.

---

## 1. System Component Boundaries

The system is split into four isolated layers containerized using **Docker Compose**:

```
+-----------------------------------------------------------------------------------+
| Host Machine                                                                      |
|  +------------------+                                                             |
|  | Local Ollama API | <--------------------------------+                          |
|  | [127.0.0.1:11434]|                                  |                          |
|  +------------------+                                  |                          |
+--------------------------------------------------------|--------------------------+
| Docker Network Bridge                                  |                          |
|  +--------------------+      HTTP API Request      +---|-----------------------+  |
|  | Nginx Web Frontend | -------------------------> | FastAPI Backend Container |  |
|  | [Port 8080:80]     |                            | [Port 8000:8000]          |  |
|  +--------------------+                            +---------------------------+  |
|                                                              |   |                |
|                                                  SQL Queries |   | pgvector       |
|                                                              v   v                |
|                                                    +----------------------------+ |
|                                                    | Postgres Database (pg16)   | |
|                                                    | [Port 5435:5432]           | |
|                                                    +----------------------------+ |
+-----------------------------------------------------------------------------------+
```

1.  **Frontend Server (Nginx):** Serves static files (`index.html`, `style.css`, `app.js`) to client browsers on host port `8080`. Connects to the backend container over HTTP.
2.  **Backend Application (FastAPI):** Exposes REST API endpoints on host port `8000`. Handles database migrations, ORM modeling, vector retrieval calculations, and routes prompts to the LLM.
3.  **Database Server (Postgres + pgvector):** Persistent database running on host port `5435`. Stores conversation history and the high-dimensional transcript vector index.
4.  **Cognitive Model Server (Ollama):** Running natively on the host machine (`localhost:11434`). The containerized backend communicates with it via the `host.docker.internal` gateway.

---

## 2. Database Schema

The database schema is declared in `db/init/01-init.sql` and mapped via SQLAlchemy ORM in `backend/app/models.py`.

### `transcript_chunks`
Stores segmented transcript elements. Contains a vector column for semantic indexing:
*   `id` (SERIAL PRIMARY KEY)
*   `video_id` (VARCHAR(255) NOT NULL)
*   `chunk_index` (INTEGER NOT NULL)
*   `chunk_text` (TEXT NOT NULL)
*   `embedding` (vector(768)) -- Configured for nomic-embed-text dimensional space
*   `guest` (VARCHAR(255))
*   `title` (TEXT)
*   `youtube_url` (TEXT)
*   `episode_metadata` (JSONB) -- publish_date, duration
*   *Constraint:* `UNIQUE(video_id, chunk_index)`

### `sessions`
Preserves user conversational sessions:
*   `id` (UUID PRIMARY KEY DEFAULT gen_random_uuid())
*   `created_at` (TIMESTAMP WITH TIME ZONE)
*   `metadata` (JSONB) -- Custom tags (e.g., session title)

### `messages`
Maintains conversational threads and response histories:
*   `id` (SERIAL PRIMARY KEY)
*   `session_id` (UUID REFERENCES sessions(id) ON DELETE CASCADE)
*   `role` (VARCHAR(20) NOT NULL) -- user, assistant, system
*   `content` (TEXT NOT NULL)
*   `citations` (JSONB) -- Array of references (guest, title, URL, video_id, chunk_index)
*   `created_at` (TIMESTAMP WITH TIME ZONE)

---

## 3. RAG Pipeline Flow

### Ingestion (CLI Script)
1.  Reads raw transcripts in `/episodes/{guest}/transcript.md`.
2.  Splits file contents into Markdown YAML frontmatter and raw body.
3.  Segments transcript into chunks of `800` characters with `150` characters overlap.
4.  Calls Ollama's `/api/embeddings` to generate a 768-dimension vector using `nomic-embed-text`.
5.  Stores chunk, metadata, and vector into `transcript_chunks` (ignores duplicates using `ON CONFLICT DO NOTHING`).

### Retrieval & Search
When a user queries the model:
1.  Generates a 768-dimension query embedding.
2.  Executes a Cosine Distance vector search against Postgres:
    ```sql
    SELECT *, (1.0 - (embedding <=> :query_embedding)) AS similarity 
    FROM transcript_chunks 
    ORDER BY embedding <=> :query_embedding 
    LIMIT 5;
    ```
3.  Filters out chunks scoring below a threshold of `0.4`.

### Prompt Routing & Generation
*   **Standard Chat Mode:** Constructs a prompt enclosing the retrieved segment texts as system context. Appends the past 10 messages from the database to maintain follow-up context.
    *   *Fallback Protection:* If no chunks score $\ge 0.4$ similarity, the prompt layer returns a static grounded denial message immediately without querying the LLM, protecting against hallucinations.
*   **Ship 30 for 30 Essay Skill:** Places retrieved context inside a strict structural prompt that enforces essay formatting (attention hook, 1200-word limit, headers, actionable takeaway, bold key details).

---

## 4. Security Sandboxing

To mitigate Cross-Site Scripting (XSS) and parent context hijacks from generated HTML/JS artifacts:
1.  The frontend rendering panel hosts a nested iframe: `<iframe sandbox="allow-scripts">`
2.  The iframe's `srcdoc` is populated directly with the AI-generated code.
3.  The sandbox blocks:
    *   `allow-same-origin`: The iframe cannot read parent site local storage, sessions, cookies, or DOM.
    *   `allow-top-navigation`: Scripts inside the artifact cannot force parent redirect hijackings.
    *   Allows only `allow-scripts` to run interactive elements (charts, tables) safely in isolation.
