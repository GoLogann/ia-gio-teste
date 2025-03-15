from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from domain.models.base import Base

class Provedor(Base):
    __tablename__ = 'provedor'
    __table_args__ = {'schema': 'gio'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(200), nullable=False)

    configuracoes = relationship("Configuracao", back_populates="provedor")
    modelos = relationship("ProvedorModelo", back_populates="provedor")

    class Config:
        from_attributes = True