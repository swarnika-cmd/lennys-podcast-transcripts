from sqlalchemy.orm import Session
from app import models, retrieval, llm, crud
from app.schemas import Citation
from uuid import UUID
from typing import Dict, Any, List, Tuple

SIMILARITY_THRESHOLD = 0.4

STANDARD_SYSTEM_PROMPT = """You are the Lenny Growth Assistant, a helpful RAG-powered chatbot designed to answer product management and growth questions.
Your answers MUST be strictly grounded in the provided transcript context.
If the context does not contain enough information to answer the question, state: "I do not have grounded information on this topic in the ingested transcripts." Do not make up any information.
Keep your response professional, precise, and highly structured.

Retrieved Context:
{context}
"""

ESSAY_SYSTEM_PROMPT = """You are the Ship 30 for 30 Essay Builder. Your task is to write a highly compelling, professional growth/product essay based on the retrieved transcript context.
Write an essay of approximately 1,200 to 1,250 words following these strict structural and formatting guidelines:
1. **Strong Hook**: Start with an attention-grabbing opening line.
2. **Clear Narrative Progression**: Flow logically from problem to framework to application.
3. **Skimmable Formatting**: Use clear, descriptive Markdown headings (H2, H3), bullet points, and **selective bold emphasis** on key takeaways.
4. **Specific, Useful Takeaway**: Conclude with a highly actionable framework, list, or step-by-step guide.
5. **Strict Grounding**: Do not hallucinate. Use only the provided context. If the context is insufficient, state: "I do not have grounded information on this topic in the ingested transcripts."

Retrieved Context:
{context}
"""

def generate_agent_response(
    db: Session,
    session_id: UUID,
    user_message: str,
    provider: str = "ollama",
    mode: str = "standard"
) -> Tuple[str, List[Dict[str, Any]]]:
    # 1. Retrieve similar chunks
    # We retrieve 5 chunks
    results = retrieval.retrieve_similar_chunks(db, user_message, limit=5, provider=provider)
    
    # 2. Filter by threshold
    valid_results = [res for res in results if res[1] >= SIMILARITY_THRESHOLD]
    
    # If no results are above similarity threshold, return the fallback message immediately
    if not valid_results:
        fallback = "I do not have grounded information on this topic in the ingested transcripts."
        # Save messages to database
        crud.create_message(db, session_id, "user", user_message, [])
        crud.create_message(db, session_id, "assistant", fallback, [])
        return fallback, []
    
    # 3. Format context and citations
    context_blocks = []
    citations = []
    
    # To avoid duplicate citations in response metadata, keep track of unique video_id/chunk_index
    seen_citations = set()
    
    for chunk, score in valid_results:
        context_blocks.append(
            f"--- START EPISODE CHUNK (Guest: {chunk.guest}, Title: {chunk.title}, Similarity: {score:.2f}) ---\n"
            f"{chunk.chunk_text}\n"
            f"--- END EPISODE CHUNK ---"
        )
        
        cit_key = (chunk.video_id, chunk.chunk_index)
        if cit_key not in seen_citations:
            seen_citations.add(cit_key)
            citations.append({
                "guest": chunk.guest,
                "title": chunk.title,
                "youtube_url": chunk.youtube_url,
                "video_id": chunk.video_id,
                "chunk_index": chunk.chunk_index
            })
            
    context_str = "\n\n".join(context_blocks)
    
    # 4. Construct System Prompt based on mode
    if mode == "essay":
        system_prompt = ESSAY_SYSTEM_PROMPT.format(context=context_str)
    else:
        system_prompt = STANDARD_SYSTEM_PROMPT.format(context=context_str)
        
    # 5. Load Session History
    db_session = crud.get_session(db, session_id)
    chat_history = []
    
    # Add system prompt first
    chat_history.append({"role": "system", "content": system_prompt})
    
    # Add last 10 messages from session to preserve context without exceeding tokens
    if db_session and db_session.messages:
        # Sort by creation time (or ID)
        sorted_msgs = sorted(db_session.messages, key=lambda m: m.id)
        for msg in sorted_msgs[-10:]:
            chat_history.append({"role": msg.role, "content": msg.content})
            
    # Add current user message
    chat_history.append({"role": "user", "content": user_message})
    
    # 6. Call LLM
    try:
        response_content = llm.chat_llm(chat_history, provider=provider)
    except Exception as e:
        print(f"[LLM CHAT ERROR] LLM generation failed: {e}")
        response_content = f"Sorry, I encountered an error communicating with the LLM provider ({provider})."
        citations = []
        
    # 7. Save to Database
    # Save the user message first
    crud.create_message(db, session_id, "user", user_message, [])
    # Save assistant message with citations
    crud.create_message(db, session_id, "assistant", response_content, citations)
    
    return response_content, citations
