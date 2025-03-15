from pydantic import BaseModel
from typing import Optional


class InnovationSummary(BaseModel):
    nivel_inovacao_p1: Optional[str] = None
    nivel_inovacao_p2: Optional[str] = None
    nivel_inovacao_p3: Optional[str] = None
    nivel_inovacao_p4: Optional[str] = None
    mod_ped_universidades: Optional[str] = None
    mod_ped_icts: Optional[str] = None
    mod_ped_parceiras: Optional[str] = None
    mod_inovacao_patente: Optional[str] = None
    mod_inovacao_fomento: Optional[str] = None
    mod_inovacao_ldb: Optional[str] = None
    mod_especifico: Optional[str] = None

    nome_solicitante: Optional[str] = None
    nome_empresa: Optional[str] = None
    nome_projeto: Optional[str] = None
    area_projeto: Optional[str] = None
    valor_investimento: Optional[float] = None
    receita_operacional_liquida: Optional[float] = None
    proporcao_pdi: Optional[float] = None