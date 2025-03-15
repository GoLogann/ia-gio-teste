import httpx

from domain.schemas.gio_schema import GioRequestSchema
from domain.schemas.usuario_schema import Usuario
from resources.api.config import AUTHMANAGERURL
from fastapi import Request, HTTPException, status

def get_usuario_by_id(request: Request, id_usuario: str) -> Usuario:
    token = request.app.state.token['access_token']
    base_url = f"{AUTHMANAGERURL}/users/{id_usuario}"
    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        with httpx.Client() as client:
            response = client.get(base_url, headers=headers)
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code= e.response.status_code,detail=str(e))

    try:
        data = response.json()
        usuario_response = Usuario(**data)
        return usuario_response
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao decodificar a resposta: {e}"
        )

def validar_e_preencher_usuario(request: Request, gio: GioRequestSchema, jwt_payload: dict) -> Usuario:
    if not gio.id_usuario:
        gio.id_usuario = jwt_payload.get("sub")

    try:
        usuario = get_usuario_by_id(request, gio.id_usuario.__str__())
        return usuario
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar a solicitação do usuário")
