import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domain.models import ProvedorModelo
from domain.models.configuracao import Configuracao
from domain.models.contexto_modelo import ContextoModelo
from domain.models.provedor import Provedor
from domain.schemas.configuracao_modelo_schema import ConfiguracaoModeloSchema
from repository.base_repository import BaseRepository
from resources.datetime_config import time_now


class ConfiguracaoRepository(BaseRepository[Configuracao]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_configuracao_by_provedor_nome(self, nome_provedor: str) -> Optional[Configuracao]:
        return (
            self.db.query(Configuracao)
            .join(Provedor, Configuracao.id_provedor == Provedor.id)
            .filter(Provedor.nome == nome_provedor)
            .first()
        )

    def add_context_to_llm_model(self, context_model: ContextoModelo):
        provedor_modelo = self.db.query(ProvedorModelo).filter(ProvedorModelo.id == context_model.id_provedor_modelo).first()
        if not provedor_modelo:
            raise HTTPException(status_code=404, detail="Provider Model not found")

        contexto_modelo = ContextoModelo(
            id=uuid.uuid4(),
            id_provedor_modelo=context_model.id_provedor_modelo,
            nome=context_model.nome,
            contexto=context_model.contexto,
            criado=time_now()
        )

        self.db.add(contexto_modelo)
        self.db.commit()
        self.db.refresh(contexto_modelo)

        return "context added successfully"

    def add_configuracao_modelo_llm(self, configuracao_modelo: ConfiguracaoModeloSchema):
        provedor = Provedor(
            nome=configuracao_modelo.provedor.nome,
            id=uuid.uuid4()
        )

        provedor_modelo = ProvedorModelo(
            id=uuid.uuid4(),
            id_provedor=provedor.id,
            nome=configuracao_modelo.provedor_modelo.nome,
            descricao=configuracao_modelo.provedor_modelo.descricao
        )

        configuracao = Configuracao(
            id=uuid.uuid4(),
            id_provedor=provedor.id,
            temperatura=configuracao_modelo.configuracao.temperatura,
            api_key=configuracao_modelo.configuracao.api_key,
            api_token=configuracao_modelo.configuracao.api_token,
            url_base=configuracao_modelo.configuracao.url_base
        )

        contexto_modelo = ContextoModelo(
            id=uuid.uuid4(),
            id_provedor_modelo=provedor_modelo.id,
            nome=configuracao_modelo.contexto_modelo.nome,
            contexto=configuracao_modelo.contexto_modelo.contexto,
            criado=time_now()
        )

        self.db.add(provedor)
        self.db.commit()
        self.db.refresh(provedor)

        self.db.add(provedor_modelo)
        self.db.commit()
        self.db.refresh(provedor_modelo)

        self.db.add(configuracao)
        self.db.commit()
        self.db.refresh(configuracao)

        self.db.add(contexto_modelo)
        self.db.commit()
        self.db.refresh(contexto_modelo)

        return "modelo adicionado"

    def delete_configuracao_modelo_llm(self, id_provedor: uuid.UUID):
        provedor = self.db.query(Provedor).filter(Provedor.id == id_provedor).first()
        if not provedor:
            raise HTTPException(status_code=404, detail="Provedor não encontrado")

        provedor_modelos = self.db.query(ProvedorModelo).filter(ProvedorModelo.id_provedor == id_provedor).all()

        for modelo in provedor_modelos:
            self.db.query(ContextoModelo).filter(ContextoModelo.id_provedor_modelo == modelo.id).delete()

        self.db.query(ProvedorModelo).filter(ProvedorModelo.id_provedor == id_provedor).delete()

        self.db.query(Configuracao).filter(Configuracao.id_provedor == id_provedor).delete()

        self.db.query(Provedor).filter(Provedor.id == id_provedor).delete()

        self.db.commit()
