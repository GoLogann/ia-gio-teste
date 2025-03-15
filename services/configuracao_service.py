from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domain.models import ProvedorModelo, Provedor, Configuracao
from domain.models.contexto_modelo import ContextoModelo
from domain.schemas.configuracao_modelo_schema import ConfiguracaoModeloSchema
from repository.configuracao_repository import ConfiguracaoRepository

class ConfiguracaoService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ConfiguracaoRepository(db)

    def add_modelo_llm(self, modelo: ConfiguracaoModeloSchema):
        try:
            resposta = self.repository.add_configuracao_modelo_llm(modelo)
        except Exception as e:
            return e

        return resposta

    def add_context_to_llm_model(self, context: ContextoModelo):
        try:
            response = self.repository.add_context_to_llm_model(context)
        except Exception as e:
            return e

        return response

    def delete_modelo_llm(self, id_provedor: UUID):
        try:
            self.repository.delete_configuracao_modelo_llm(id_provedor)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao deletar modelo: {str(e)}")

    def get_todos_modelos(self):
        modelos = (
            self.db.query(ProvedorModelo)
            .join(Provedor, ProvedorModelo.id_provedor == Provedor.id)
            .outerjoin(ContextoModelo, ContextoModelo.id_provedor_modelo == ProvedorModelo.id)
            .all()
        )

        resultado = []
        for modelo in modelos:
            resultado.append({
                "id": str(modelo.id),
                "nome": modelo.nome,
                "descricao": modelo.descricao,
                "id_provedor": str(modelo.id_provedor),
                "id_provedor_modelo": str(modelo.id),
                "contextos": [
                    {
                        "id": str(contexto.id),
                        "nome": contexto.nome,
                        "contexto": contexto.contexto
                    }
                    for contexto in modelo.contextos
                ]
            })
        return resultado

    def atualizar_modelo(self, modelo_id: str, modelo: ConfiguracaoModeloSchema):
        try:
            provedor_modelo = self.db.query(ProvedorModelo).filter(ProvedorModelo.id == modelo_id).first()
            if not provedor_modelo:
                raise Exception("Modelo não encontrado")


            provedor_modelo.nome = modelo.provedor_modelo.nome
            provedor_modelo.descricao = modelo.provedor_modelo.descricao

            configuracao = self.db.query(Configuracao).filter(
                Configuracao.id_provedor == provedor_modelo.id_provedor).first()
            if configuracao:
                configuracao.temperatura = modelo.configuracao.temperatura
                configuracao.api_key = modelo.configuracao.api_key
                configuracao.api_token = modelo.configuracao.api_token
                configuracao.url_base = modelo.configuracao.url_base

            contextos = self.db.query(ContextoModelo).filter(ContextoModelo.id_provedor_modelo == modelo_id).all()
            for contexto in contextos:
                if contexto.id == modelo.contexto_modelo.id:
                    contexto.nome = modelo.contexto_modelo.nome
                    contexto.contexto = modelo.contexto_modelo.contexto

            self.db.commit()
            return provedor_modelo
        except Exception as e:
            self.db.rollback()
            raise e

