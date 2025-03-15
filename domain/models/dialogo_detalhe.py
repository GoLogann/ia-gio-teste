from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, column_property
from datetime import datetime
import uuid
from domain.models.base import Base

class DialogoDetalhe(Base):
    __tablename__ = 'dialogo_detalhe'
    __table_args__ = {'schema': 'gio'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_dialogo = Column(UUID(as_uuid=True), ForeignKey('gio.dialogo.id'), nullable=False)
    pergunta = Column(Text, nullable=False)
    resposta = Column(Text, nullable=False)
    insight = Column(Text)
    token = Column(Integer, default=0)
    criado = Column(DateTime, default=datetime.utcnow, nullable=False)

    dialogo = relationship("Dialogo", back_populates="dialogoDetalhes")

    idDialogo = column_property(id_dialogo)