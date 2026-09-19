from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from src.db.postgres import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    source_name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    content_hash = Column(String, nullable=False)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)
    tags = Column(JSONB, nullable=True)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    text_content = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    document = relationship("Document", backref="chunks")
