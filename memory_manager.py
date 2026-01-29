import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    create_engine,
    select,
    or_,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Please add it to your .env file, "
        "for example: postgresql://user:password@host:port/dbname"
    )

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.timestamp.asc()",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String, ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


Base.metadata.create_all(engine)


def _to_conv_dict(conv: Conversation) -> Dict[str, Any]:
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in conv.messages
        ],
    }


def ensure_user_storage(user_id: str) -> None:
    """No-op for DB-backed storage; kept for API compatibility."""
    if not user_id:
        raise ValueError("user_id must be non-empty")


def list_conversations(user_id: str) -> List[Dict[str, Any]]:
    with SessionLocal() as session:
        convs = (
            session.execute(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
            )
            .scalars()
            .all()
        )
        # Eagerly load messages for each conversation
        for conv in convs:
            _ = conv.messages
        return [_to_conv_dict(conv) for conv in convs]


def create_new_conversation(user_id: str, title: str = "New conversation") -> Dict[str, Any]:
    ensure_user_storage(user_id)
    now = datetime.utcnow()
    conv = Conversation(user_id=user_id, title=title, created_at=now, updated_at=now)
    with SessionLocal() as session:
        session.add(conv)
        session.commit()
        session.refresh(conv)
        _ = conv.messages
        return _to_conv_dict(conv)


def get_conversation(user_id: str, conv_id: str) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        conv = (
            session.execute(
                select(Conversation).where(
                    Conversation.id == conv_id, Conversation.user_id == user_id
                )
            )
            .scalars()
            .first()
        )
        if not conv:
            return None
        _ = conv.messages
        return _to_conv_dict(conv)


def append_message(
    user_id: str,
    conv_id: str,
    role: str,
    content: str,
) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        conv = (
            session.execute(
                select(Conversation).where(
                    Conversation.id == conv_id, Conversation.user_id == user_id
                )
            )
            .scalars()
            .first()
        )
        if not conv:
            return None
        msg = Message(conversation_id=conv.id, role=role, content=content)
        conv.updated_at = datetime.utcnow()
        session.add(msg)
        session.commit()
        session.refresh(conv)
        _ = conv.messages
        return _to_conv_dict(conv)


def rename_conversation(user_id: str, conv_id: str, new_title: str) -> None:
    with SessionLocal() as session:
        conv = (
            session.execute(
                select(Conversation).where(
                    Conversation.id == conv_id, Conversation.user_id == user_id
                )
            )
            .scalars()
            .first()
        )
        if conv:
            conv.title = new_title
            conv.updated_at = datetime.utcnow()
            session.commit()


def search_conversations(user_id: str, query: str) -> List[Dict[str, Any]]:
    """Case-insensitive substring search over titles and messages, per user."""
    pattern = f"%{query.lower()}%"
    with SessionLocal() as session:
        conv_alias = Conversation
        msg_alias = Message

        stmt = (
            select(conv_alias)
            .distinct()
            .outerjoin(msg_alias, msg_alias.conversation_id == conv_alias.id)
            .where(
                conv_alias.user_id == user_id,
                or_(
                    conv_alias.title.ilike(pattern),
                    msg_alias.content.ilike(pattern),
                ),
            )
            .order_by(conv_alias.updated_at.desc())
        )
        convs = session.execute(stmt).scalars().all()
        for conv in convs:
            _ = conv.messages
        return [_to_conv_dict(conv) for conv in convs]

