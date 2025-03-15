from datetime import date
from pydantic import BaseModel
from typing import Optional, List


class AdministrativoParameterResponse(BaseModel):
    id: Optional[int] = None
    nome: Optional[str] = None
    valor: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

class SituacaoCadastral(BaseModel):
    codigo: Optional[str] = None
    data: Optional[date] = None
    motivo: Optional[str] = None

class NaturezaJuridica(BaseModel):
    codigo: Optional[str] = None
    descricao: Optional[str] = None

class CNAE(BaseModel):
    codigo: Optional[str] = None
    descricao: Optional[str] = None

class Municipio(BaseModel):
    codigo: Optional[str] = None
    descricao: Optional[str] = None

class Pais(BaseModel):
    codigo: Optional[str] = None
    descricao: Optional[str] = None

class Endereco(BaseModel):
    tipoLogradouro: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    cep: Optional[str] = None
    bairro: Optional[str] = None
    municipio: Optional[Municipio] = None
    uf: Optional[str] = None
    pais: Optional[Pais] = None

class Telefone(BaseModel):
    ddd: Optional[str] = None
    numero: Optional[str] = None

class CNPJSchema(BaseModel):
    ni: Optional[str] = None
    tipoEstabelecimento: Optional[str] = None
    nomeEmpresarial: Optional[str] = None
    nomeFantasia: Optional[str] = None
    situacaoCadastral: Optional[SituacaoCadastral] = None
    naturezaJuridica: Optional[NaturezaJuridica] = None
    dataAbertura: Optional[date] = None
    cnaePrincipal: Optional[CNAE] = None
    cnaeSecundarias: Optional[List[CNAE]] = None
    endereco: Optional[Endereco] = None
    municipioJurisdicao: Optional[Municipio] = None
    telefones: Optional[List[Telefone]] = None
    correioEletronico: Optional[str] = None
    capitalSocial: Optional[int] = None
    porte: Optional[str] = None
    situacaoEspecial: Optional[str] = None
    dataSituacaoEspecial: Optional[str] = None
    informacoesAdicionais: Optional[str] = None
    socios: Optional[List[dict]] = None
