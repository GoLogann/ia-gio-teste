import math

from fastapi import HTTPException
from sqlalchemy import func, distinct, desc, asc, Row, RowMapping
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Type, Tuple, Any, Dict, Union, Sequence

from domain.models.base import Base
from domain.models.dialogo import Dialogo
from domain.models.dialogo_detalhe import DialogoDetalhe
from domain.schemas.dialogo_schema import DialogoSchema, DialogoDetalheSchema
from repository.base_repository import BaseRepository


class Pageable:
    def __init__(self, content: List[Any], page: int, size: int, total_elements: int):
        self.content = content
        self.page = page
        self.size = size
        self.total_elements = total_elements
        self.total_pages = math.ceil(total_elements / size)
        self.first = page == 1
        self.last = page == self.total_pages
        self.number_of_elements = len(content)
        self.empty = len(content) == 0

class DialogoRepository(BaseRepository[Dialogo]):
    def __init__(self, db: Session):
        super().__init__(db)

    async def fetch_message_history_from_db(self, dialogue_id: str) -> Sequence[Row[Any] | RowMapping | Any]:
        query = (
            self.db.query(DialogoDetalhe)
            .where(DialogoDetalhe.id_dialogo == dialogue_id)
            .order_by(asc(DialogoDetalhe.criado))
        )

        result =  self.db.execute(query)
        return result.scalars().all()

    def get_dialogo_by_id(self, dialogo_id: str) -> Optional[Dialogo]:
        return self.db.query(Dialogo).filter(Dialogo.id == dialogo_id).first()

    def get_dialog_by_user_id(self, user_id: str) -> Optional[Dialogo]:
        return (
            self.db.query(Dialogo)
            .filter(Dialogo.id_usuario == user_id)
            .first()
        )

    def get_last_dialogo_with_detalhes_by_user_id(self, user_id: str) -> Optional[DialogoSchema]:
        ultimo_dialogo = (
            self.db.query(Dialogo)
            .filter_by(id_usuario=user_id)
            .order_by(desc(Dialogo.criado))
            .first()
        )

        if not ultimo_dialogo:
            return None

        dialogo_detalhes_ordenados = (
            self.db.query(DialogoDetalhe)
            .filter(DialogoDetalhe.id_dialogo == ultimo_dialogo.id)
            .order_by(asc(DialogoDetalhe.criado))
            .all()
        )

        detalhes_schemas = [
            DialogoDetalheSchema(
                id=detalhe.id,
                idDialogo=detalhe.id,
                pergunta=detalhe.pergunta,
                resposta=detalhe.resposta,
                insight=detalhe.insight,
                token=detalhe.token,
                criado=detalhe.criado,
            )
            for detalhe in dialogo_detalhes_ordenados
        ]

        dialogo_schema = DialogoSchema(
            id=ultimo_dialogo.id,
            id_usuario=ultimo_dialogo.id_usuario,
            tipo=ultimo_dialogo.tipo,
            criado=ultimo_dialogo.criado,
            dialogoDetalhes=detalhes_schemas
        )

        return dialogo_schema
    def get_dialogo_details(self, dialogo_id: str) -> List[DialogoDetalhe]:
        return self.db.query(DialogoDetalhe).filter(DialogoDetalhe.id_dialogo == dialogo_id).all()

    def get_last_dialogo_by_user(self, id_usuario: str, tipo: int) -> Optional[str]:
        try:
            dialogo = self.db.query(Dialogo.id).filter(
                Dialogo.id_usuario == id_usuario,
                Dialogo.tipo == tipo
            ).order_by(Dialogo.criado.desc()).limit(1).one_or_none()
            return dialogo[0] if dialogo else None
        except Exception as e:
            print(f"Erro ao buscar o último diálogo: {e}")
            return None

    def entity_exist(self, model: Type[Base], id: str) -> Tuple[Any, bool]:
        print(f"Verificando existência da entidade: {model.__name__} com ID: {id}")
        instance = self.db.query(model).get(id)
        if instance:
            return instance, True
        else:
            return None, False

    def listar_historico_perguntas_respostas(self, id_usuario: str, id_dialogo: str, tipo: int) -> Dialogo | None:
        try:
            query = self.db.query(Dialogo).options(
                joinedload(Dialogo.dialogoDetalhes)
            ).filter(
                Dialogo.id == id_dialogo,
                Dialogo.id_usuario == id_usuario,
                Dialogo.tipo == tipo
            )

            dialogo = query.one_or_none()
            if dialogo is None:
                raise HTTPException(status_code=404,
                                    detail="Não foi encontrado nenhum diálogo correspondente aos critérios.")

            return dialogo
        except HTTPException as e:
            print(f"HTTPException ao listar histórico: {e}")
            raise e
        except Exception as e:
            print(f"Erro durante a consulta do histórico de diálogos: {e}")
            raise HTTPException(status_code=500, detail=f"Erro durante a consulta do histórico de diálogos: {e}")

    def listar_historico_dialogo(self, page_size: int, page: int, order_by: str, filtro: Dict) -> Pageable:
        if page <= 0:
            page = 1

        query = self.db.query(Dialogo).options(
            joinedload(Dialogo.dialogoDetalhes)
        ).join(
            DialogoDetalhe, Dialogo.id == DialogoDetalhe.id_dialogo, isouter=True
        ).filter(
            Dialogo.id_usuario == filtro['id_usuario'],
            Dialogo.tipo == filtro['tipo']
        ).group_by(Dialogo.id)

        total_elements = self.db.query(func.count(distinct(Dialogo.id))).filter(
            Dialogo.id_usuario == filtro['id_usuario'],
            Dialogo.tipo == filtro['tipo']
        ).scalar()

        if total_elements == 0:
            return Pageable([], page, page_size, total_elements)

        pages = math.ceil(total_elements / page_size)

        if page > pages:
            raise HTTPException(status_code=400, detail="pagination out of correct range")

        offset = (page - 1) * page_size

        if order_by:
            order_by_column, order_by_direction = order_by.split()
            if order_by_column not in ['criado']:
                raise HTTPException(status_code=400, detail=f"Invalid order by column: {order_by_column}")

            order_by_column = getattr(Dialogo, order_by_column)

            if order_by_direction.lower() == 'desc':
                query = query.order_by(desc(order_by_column))
            else:
                query = query.order_by(asc(order_by_column))

        query = query.offset(offset).limit(page_size)

        results = query.all()

        return Pageable(results, page, page_size, total_elements)


def fetch_chat_history(id_usuario: str, tipo_dialogo: int, id_dialogo: str, db: Session) -> Union[Dialogo, None]:
    repository = DialogoRepository(db)

    response = repository.listar_historico_perguntas_respostas(id_usuario=id_usuario, id_dialogo=id_dialogo, tipo=tipo_dialogo)

    return response