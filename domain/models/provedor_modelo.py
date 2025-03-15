from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from domain.models.base import Base

class ProvedorModelo(Base):
    __tablename__ = 'provedor_modelo'
    __table_args__ = {'schema': 'gio'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_provedor = Column(UUID(as_uuid=True), ForeignKey('gio.provedor.id'), nullable=False)
    nome = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=False)

    provedor = relationship("Provedor", back_populates="modelos")

    contextos = relationship("ContextoModelo", back_populates="provedor_modelo")
