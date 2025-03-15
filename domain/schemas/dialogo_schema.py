from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class DialogoListHistory(BaseModel):
    idUsuario: str = None
    idDialogo: Optional[str] = None
    tipo: Optional[int] = None


class DialogoDetalheSchema(BaseModel):
    id: UUID
    idDialogo: UUID
    pergunta: str
    resposta: str
    insight: Optional[str] = None
    token: int
    criado: datetime

    class Config:
        from_attributes = True


class DialogoSchema(BaseModel):
    id: UUID
    id_usuario: UUID
    tipo: int
    criado: datetime
    dialogoDetalhes: List[DialogoDetalheSchema]

    class Config:
        from_attributes = True

class DescricaoSchema(BaseModel):
    id: UUID
    id_usuario: UUID
    tipo: int
    criado: datetime
    descricao: str

    class Config:
        from_attributes = True
