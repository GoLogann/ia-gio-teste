import uuid

from domain.models import Dialogo, DialogoDetalhe
from repository.base_repository import BaseRepository


class ChatBotRepository(BaseRepository):
    def get_dialogo_by_usuario(self, id_comunicacao_enxame_contato: str):
        try:
            return self.db.query(Dialogo).filter(Dialogo.id_usuario == id_comunicacao_enxame_contato).first()
        except Exception as e:
            self.db.rollback()
            raise

    def get_respostas_by_dialogo(self, id_dialogo: uuid.UUID):
        try:
            return self.db.query(DialogoDetalhe).filter(DialogoDetalhe.id_dialogo == id_dialogo).all()
        except Exception as e:
            self.db.rollback()
            raise