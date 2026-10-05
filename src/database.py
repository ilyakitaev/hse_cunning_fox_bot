"""Database module for system data storage using PostgreSQL."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload

from config import Config

Base = declarative_base()

engine = create_engine(Config().DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> SessionLocal:
    """Get database session."""
    return SessionLocal()


# ============ Models ============


class User(Base):
    """User model for authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    authorized = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SystemPrompt(Base):
    """System prompt model."""
    __tablename__ = "system_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    prompt_data = Column(Text, nullable=False)
    author_telegram_username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    assistants = relationship("Assistant", back_populates="system_prompt")


class Collection(Base):
    """Collection model for system database."""
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assistants = relationship("Assistant", back_populates="collection")


class Assistant(Base):
    """Assistant model."""
    __tablename__ = "assistants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    system_prompt_id = Column(Integer, ForeignKey("system_prompts.id"), nullable=False)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False)
    score_threshold = Column(Float, default=0.6, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    system_prompt = relationship("SystemPrompt", back_populates="assistants")
    collection = relationship("Collection", back_populates="assistants")


# ============ Database Operations ============


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Get user by telegram ID."""
    session = get_session()
    try:
        return session.query(User).filter(User.telegram_id == telegram_id).first()
    finally:
        session.close()


def create_or_update_user(telegram_id: int, authorized: bool) -> User:
    """Create or update user."""
    session = get_session()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.authorized = authorized
        else:
            user = User(telegram_id=telegram_id, authorized=authorized)
            session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def is_user_authorized(telegram_id: int) -> bool:
    """Check if user is authorized."""
    user = get_user_by_telegram_id(telegram_id)
    return user is not None and user.authorized


def authorize_user(telegram_id: int) -> None:
    """Authorize a user."""
    create_or_update_user(telegram_id, authorized=True)


def get_all_prompts() -> list[SystemPrompt]:
    """Get all prompts."""
    session = get_session()
    try:
        return session.query(SystemPrompt).all()
    finally:
        session.close()


def get_prompt_by_id(prompt_id: int) -> Optional[SystemPrompt]:
    """Get prompt by ID."""
    session = get_session()
    try:
        return session.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
    finally:
        session.close()


def get_prompt_by_name(name: str) -> Optional[SystemPrompt]:
    """Get prompt by name."""
    session = get_session()
    try:
        return session.query(SystemPrompt).filter(SystemPrompt.name == name).first()
    finally:
        session.close()


def create_prompt(name: str, prompt_data: str, author_username: Optional[str] = None) -> SystemPrompt:
    """Create a new prompt."""
    session = get_session()
    try:
        prompt = SystemPrompt(
            name=name,
            prompt_data=prompt_data,
            author_telegram_username=author_username,
        )
        session.add(prompt)
        session.commit()
        session.refresh(prompt)
        return prompt
    finally:
        session.close()


def update_prompt(prompt_id: int, prompt_data: str) -> Optional[SystemPrompt]:
    """Update prompt content."""
    session = get_session()
    try:
        prompt = session.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
        if prompt:
            prompt.prompt_data = prompt_data
            session.commit()
            session.refresh(prompt)
        return prompt
    finally:
        session.close()


def get_all_collections() -> list[Collection]:
    """Get all collections."""
    session = get_session()
    try:
        return session.query(Collection).all()
    finally:
        session.close()


def get_collection_by_name(name: str) -> Optional[Collection]:
    """Get collection by name."""
    session = get_session()
    try:
        return session.query(Collection).filter(Collection.name == name).first()
    finally:
        session.close()


def create_collection(name: str, description: Optional[str] = None) -> Collection:
    """Create a new collection."""
    session = get_session()
    try:
        collection = Collection(name=name, description=description)
        session.add(collection)
        session.commit()
        session.refresh(collection)
        return collection
    finally:
        session.close()


def get_all_assistants() -> list[Assistant]:
    """Get all assistants with relationships."""
    session = get_session()
    try:
        return (
            session.query(Assistant)
            .options(joinedload(Assistant.system_prompt), joinedload(Assistant.collection))
            .all()
        )
    finally:
        session.close()


def get_assistant_by_id(assistant_id: int) -> Optional[Assistant]:
    """Get assistant by ID with relationships."""
    session = get_session()
    try:
        return (
            session.query(Assistant)
            .options(joinedload(Assistant.system_prompt), joinedload(Assistant.collection))
            .filter(Assistant.id == assistant_id)
            .first()
        )
    finally:
        session.close()


def create_assistant(
    name: str,
    collection_id: int,
    system_prompt_id: int,
    score_threshold: float = 0.6
) -> Assistant:
    """Create a new assistant."""
    session = get_session()
    try:
        assistant = Assistant(
            name=name,
            collection_id=collection_id,
            system_prompt_id=system_prompt_id,
            score_threshold=score_threshold,
        )
        session.add(assistant)
        session.commit()
        session.refresh(assistant)
        return assistant
    finally:
        session.close()
