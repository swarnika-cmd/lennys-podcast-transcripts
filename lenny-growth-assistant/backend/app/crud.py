from sqlalchemy.orm import Session
from app import models, schemas
from uuid import UUID
from typing import List

def create_session(db: Session, session_in: schemas.SessionCreate) -> models.Session:
    db_session = models.Session(session_metadata=session_in.metadata)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: UUID) -> models.Session:
    return db.query(models.Session).filter(models.Session.id == session_id).first()

def get_sessions(db: Session, limit: int = 20) -> List[models.Session]:
    return db.query(models.Session).order_by(models.Session.created_at.desc()).limit(limit).all()

def create_message(db: Session, session_id: UUID, role: str, content: str, citations: list = None) -> models.Message:
    db_message = models.Message(
        session_id=session_id,
        role=role,
        content=content,
        citations=citations
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message
