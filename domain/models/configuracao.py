from sqlalchemy import Column, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from domain.models.base import Base

class Configuracao(Base):
    __tablename__ = 'configuracao'
    __table_args__ = {'schema': 'gio'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_provedor = Column(UUID(as_uuid=True), ForeignKey('gio.provedor.id'), nullable=False)
    temperatura = Column(Numeric(25, 10), default=0, nullable=False)
    api_key = Column(Text)
    api_token = Column(Text)
    url_base = Column(Text, nullable=False)

    provedor = relationship("Provedor", back_populates="configuracoes")
