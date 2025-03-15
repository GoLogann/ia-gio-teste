from typing import Optional
from sqlalchemy.orm import Session

from domain.models.contexto_modelo import ContextoModelo
from repository.base_repository import BaseRepository

class ContextoModeloRepository(BaseRepository[ContextoModelo]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_contexto_by_nome(self, nome_contexto: str) -> Optional[ContextoModelo]:
        """
        Busca um contexto pelo nome.
        :param nome_contexto: Nome do contexto que se deseja buscar.
        :return: Instância de ContextoModelo ou None se não encontrado.
        """
        return (
            self.db.query(ContextoModelo)
            .filter(ContextoModelo.nome == nome_contexto)
            .first()
        )
