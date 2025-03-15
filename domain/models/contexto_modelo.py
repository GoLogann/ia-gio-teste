from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from domain.models.base import Base
from resources.datetime_config import time_now

class ContextoModelo(Base):
    __tablename__ = 'contexto_modelo'
    __table_args__ = {'schema': 'gio'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_provedor_modelo = Column(UUID(as_uuid=True), ForeignKey('gio.provedor_modelo.id'), nullable=False)
    nome = Column(String(200), nullable=False)
    contexto = Column(Text, nullable=False)
    criado = Column(TIMESTAMP, nullable=False, default=time_now())

    provedor_modelo = relationship("ProvedorModelo", back_populates="contextos")