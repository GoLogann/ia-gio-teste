from fastapi import UploadFile
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class GioRequestSchema(BaseModel):
    """
    Schema para representar a requisição enviada pelo front-end para criar ou atualizar um diálogo.
    """
    id_usuario: Optional[UUID] = Field(None, alias='idUsuario')
    id_dialogo: Optional[UUID] = Field(None, alias='idDialogo')
    questao: Optional[str]
    contexto_questionamento: Optional[str] = Field(None, alias='contextoQuestionamento')
    contexto_embasamento: Optional[str] = Field(None, alias='contextoEmbasamento')
    contexto_opcional: Optional[str] = Field(None, alias='contextoOpcional')

    class Config:
        populate_by_name = True
        from_attributes = True

class GioDescricaoSchema(BaseModel):
    """
    Schema para representar a requisição enviada pelo front-end para gerar uma descrição completa de uma tarefa.
    """
    id_usuario: Optional[UUID] = Field(None, alias='idUsuario')
    id_dialogo: Optional[UUID] = Field(None, alias='idDialogo')
    tipo: Optional[int]
    titulo: Optional[str]
    breve_descricao: Optional[str] = Field(None, alias='breveDescricao')

    class Config:
        populate_by_name = True
        from_attributes = True

class GioResumoSchema(BaseModel):
    """
    Schema para representar a requisição de geração de um resumo completo a partir de uma transcrição de uma reunião.
    """
    id_usuario: Optional[UUID] = Field(None, alias='idUsuario')
    id_reuniao: Optional[UUID] = Field(None, alias='idReuniao')
    transcricao: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True

class GioScrapingSchema(BaseModel):
    """
    Schema para representar a requisição de geração de scraping a partir de dados minerados em URL.
    """
    id_usuario: Optional[UUID] = Field(None, alias='idUsuario')
    id_reuniao: Optional[UUID] = Field(None, alias='idReuniao')
    url: str = Field(None, alias='url')

    class Config:
        populate_by_name = True
        from_attributes = True


class ComunicacaoEnxameContatoSchema(BaseModel):
    """
    Schema para representar os dados de comunicação de um contato do enxame.
    """
    id: Optional[UUID] = Field(None, alias='id')
    id_departamento: Optional[int] = Field(None, alias='idDepartamento')
    id_dialogo: Optional[UUID] = Field(None, alias='idDialogo')
    id_usuario: Optional[UUID] = Field(None, alias='idUsuario')
    questao: Optional[str]
    nome: Optional[str]
    telefone: Optional[str]
    email: Optional[str]
    status_contato: Optional[str] = Field(None, alias='statusContato')
    modelo_ata_formatado: Optional[str] = Field(None, alias='modeloAtaReuniaoFormatado')

    class Config:
        populate_by_name = True
        from_attributes = True

class GioRequestSchemaInnovationAward(BaseModel):
    """
    Schema to represent the request sent by the front-end to create or update a dialogue.
    """
    user_id: Optional[UUID]
    dialogue_id: Optional[UUID] = Field(None, alias='dialogueId')
    specific_context_identifier: Optional[int]
    company_name: Optional[str]
    question: Optional[str]
    user_name: Optional[str] = Field(None, alias='userName')
    project_name: Optional[str] = Field(None, alias='projectName')
    project_area: Optional[str] = Field(None, alias='projectArea')
    investment_value: Optional[float] = Field(None, alias='investmentValue')
    net_operational_revenue: Optional[float] = Field(None, alias='netOperationalRevenue')
    pdi_proportion: Optional[float] = Field(None, alias='pdiProportion')

    class Config:
        populate_by_name = True
        from_attributes = True