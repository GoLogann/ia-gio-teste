from fastapi import HTTPException, Depends
from jose import jwt, JWTError
from auth.jwks import get_public_key
from auth.security import api_key_header
from typing import Optional

async def validate_jwt_token(api_key: str = Depends(api_key_header), audience: Optional[str] = "account"):
    """
    Valida o token JWT fornecido no cabeçalho Authorization.
    """
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]

    try:
        public_key = get_public_key()
        payload = jwt.decode(api_key, public_key, algorithms=["RS256"], audience=audience)
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=403,
            detail="Credenciais de autenticação inválidas: falha na decodificação do token"
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na autenticação: {str(e)}"
        )
