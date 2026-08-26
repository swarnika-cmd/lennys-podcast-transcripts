from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
from typing import List

from app.database import get_db
from app.config import settings
from app import schemas, crud, agent

app = FastAPI(
    title="The Lenny Growth Assistant API",
    description="Backend API for querying Lenny's Podcast transcripts with pgvector and dynamic LLM configurations.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        # Ping database
        db.execute(text("SELECT 1"))
    except Exception as e:
        print(f"[HEALTH CHECK ERROR] Database connection failed: {e}")
        db_status = "disconnected"
        
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "default_provider": settings.default_llm_provider,
        "ollama_url": settings.ollama_url
    }

@app.post("/sessions", response_model=schemas.SessionOut, status_code=status.HTTP_201_CREATED)
def create_chat_session(session_in: schemas.SessionCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_session(db, session_in)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@app.get("/sessions", response_model=List[schemas.SessionOut])
def list_chat_sessions(limit: int = 20, db: Session = Depends(get_db)):
    return crud.get_sessions(db, limit=limit)

@app.get("/sessions/{session_id}", response_model=schemas.SessionOut)
def get_chat_session(session_id: UUID, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session

@app.post("/sessions/{session_id}/chat", response_model=schemas.ChatResponse)
def send_chat_message(
    session_id: UUID,
    chat_req: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    # Verify session exists
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
        
    # Get provider and mode
    provider = chat_req.provider or settings.default_llm_provider
    mode = chat_req.mode or "standard"
    
    # Verify if credentials exist for the selected cloud provider
    if provider == "openai" and not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenAI API key not configured on host. Please update .env or select another model."
        )
    if provider == "anthropic" and not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anthropic API key not configured on host. Please update .env or select another model."
        )
        
    # Generate response
    response_content, citations = agent.generate_agent_response(
        db=db,
        session_id=session_id,
        user_message=chat_req.message,
        provider=provider,
        mode=mode
    )
    
    return schemas.ChatResponse(
        content=response_content,
        citations=citations,
        provider=provider,
        mode=mode
    )
