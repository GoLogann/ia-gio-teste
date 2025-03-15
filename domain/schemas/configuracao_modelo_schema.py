from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class Provedor(BaseModel):
    id: Optional[UUID] = None
    nome: str

    class Config:
        from_attributes = True

class ProvedorModelo(BaseModel):
    id: Optional[UUID] = None
    id_provedor: Optional[UUID] = None
    nome: str
    descricao: str

    class Config:
        from_attributes = True

class Configuracao(BaseModel):
    id: Optional[UUID] = None
    id_provedor: Optional[UUID] = None
    temperatura: Decimal
    api_key: Optional[str] = None
    api_token: Optional[str] = None
    url_base: str

    class Config:
        from_attributes = True

class ContextoModelo(BaseModel):
    id: Optional[UUID] = None
    id_provedor_modelo: Optional[UUID] = None
    nome: Optional[str]
    contexto: Optional[str]
    criado: Optional[datetime] = None

class ConfiguracaoModeloSchema(BaseModel):
    configuracao: Optional[Configuracao] = None
    provedor: Optional[Provedor] = None
    provedor_modelo: Optional[ProvedorModelo] = None
    contexto_modelo: Optional[ContextoModelo] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
