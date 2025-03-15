from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header, UploadFile, File
from typing import Any
from dataprovider.api.administrativo import consultar_cnpj
from constantes_globais.apiuri import ADMINISTRATIVO_URI_V2

adm = APIRouter()

@adm.get(ADMINISTRATIVO_URI_V2 + "/consulta-basica-cnpj", status_code=status.HTTP_200_OK)
def conultar_cnpj(cnpj: str, request: Request) -> Any:
    try:
        dados_cnpj = consultar_cnpj(request, cnpj)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro a realizar a consulta: {str(e)}"
        )

    return dados_cnpj
