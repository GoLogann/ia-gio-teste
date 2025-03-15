from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class Grupos(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class AcessoCentrosCustos(BaseModel):
    id: int
    idCentroCusto: int

    class Config:
        from_attributes = True


class Acesso(BaseModel):
    id: Optional[int] = None
    idEmpresa: Optional[int] = None
    idUsuario: Optional[str] = None
    idTipoUsuario: Optional[int] = None
    tipoUsuario: Optional[str] = None
    idNivelAprovacaoAdmin: Optional[int] = None
    nivelAprovacaoAdmin: Optional[str] = None
    acessoCentrosCustos: List[AcessoCentrosCustos] = []
    centroCustoTotal: Optional[bool] = None

    class Config:
        from_attributes = True


class Usuario(BaseModel):
    id: UUID
    email: Optional[str] = None
    username: Optional[str] = None
    enabled: Optional[bool] = None
    groups: List[Grupos] = []
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    full_name: Optional[str] = Field(None, alias="fullName")
    acesso: Optional[Acesso] = None
    roles: List[str] = []

    class Config:
        from_attributes = True
        populate_by_name = True
