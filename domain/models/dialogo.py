from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from domain.models.base import Base
from resources.datetime_config import time_now

class Dialogo(Base):
    __tablename__ = 'dialogo'
    __table_args__ = {'schema': 'gio'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), nullable=False)
    tipo = Column(Integer, nullable=False)
    criado = Column(DateTime, default=time_now(), nullable=False)

    dialogoDetalhes = relationship("DialogoDetalhe", back_populates="dialogo", cascade="all, delete-orphan", order_by="desc(DialogoDetalhe.criado)")