from sqlalchemy import Column, Text, DateTime, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID
import uuid
from domain.models.base import Base
from resources.datetime_config import time_now


class ProjectData(Base):
    __tablename__ = 'project_data'
    __table_args__ = {'schema': 'gio'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    criado = Column(DateTime, default=time_now(), nullable=False)
    atualizado = Column(DateTime, default=time_now(), onupdate=time_now(), nullable=False)
    nome_projeto = Column(Text, nullable=True)
    pesquisa_relacionada = Column(Text, nullable=True)
    responsavel = Column(Text, nullable=True)
    area_responsavel = Column(Text, nullable=True)
    objetivo_projeto = Column(Text, nullable=True)
    beneficio = Column(Text, nullable=True)
    diferencial = Column(Text, nullable=True)
    marco = Column(Text, nullable=True)
    desafio = Column(Text, nullable=True)
    metodologia = Column(Text, nullable=True)
    proximo_passo = Column(Text, nullable=True)
    detalhe_adicional = Column(Text, nullable=True)
    observacao_usuario = Column(Text, nullable=True)
    aprovado = Column(Boolean, default=False, nullable=False)
    dialog_id = Column(UUID(as_uuid=True), nullable=True)
    id_comunicacao_enxame_contato = Column(UUID(as_uuid=True), nullable=False)
    id_departamento = Column(BigInteger, nullable=False)

    def __repr__(self):
        return f"<ProjectData(id={self.id}, nome_projeto={self.nome_projeto}, criado={self.criado})>"
