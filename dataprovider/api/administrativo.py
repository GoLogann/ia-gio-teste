import httpx
from fastapi import Request, HTTPException, status
from domain.schemas.administrativo_schema import AdministrativoParameterResponse, CNPJSchema
from resources.api.config import ADMINISTRATIVOURL
from domain.schemas.gio_schema import GioRequestSchema as Gio


def get_parameter_by_name(request: Request, nome: str) -> str:
    """
    Busca um parâmetro administrativo pelo nome através de uma chamada a API externa.
    """
    token = request.app.state.token['access_token']
    base_url = f"{ADMINISTRATIVOURL}/parametros/obter-valor-por-nome"
    params = {'nome': nome}

    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        with httpx.Client() as client:
            response = client.get(base_url, params=params, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

    try:
        data = response.json()
        param_response = AdministrativoParameterResponse(**data)
        return param_response.valor
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao decodificar a resposta: {e}"
        )

def consultar_cnpj(request: Request, cnpj: str) -> CNPJSchema:
    token = request.app.state.token['access_token']
    base_url = f"{ADMINISTRATIVOURL}/integracoes/serpro/consulta-basica-cnpj/{cnpj}"

    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        with httpx.Client() as client:
            response = client.get(base_url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

    try:
        data = response.json()
        return CNPJSchema(**data)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao decodificar a resposta: {e}"
        )

def substitute_values_in_script(request: Request, gio: Gio) -> str:
    """
    Substitui valores no script de contestação com base no contexto fornecido no objeto Gio.
    Busca um script administrativo padrão e substitui os placeholders pelos contextos do Gio.
    """
    script_contestacao = get_parameter_by_name(request=request, nome="SCRIPT_CONTESTACAO_MCTI")

    valores_substituicao = {
        "contestacao": gio.contexto_questionamento or "",
        "projeto": gio.contexto_embasamento or "",
        "opcional": gio.contexto_opcional or ""
    }

    for key, value in valores_substituicao.items():
        if value:
            placeholder = f"${{{key}}}"
            script_contestacao = script_contestacao.replace(placeholder, value)

    return script_contestacao