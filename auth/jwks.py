import requests
from jose.utils import base64url_decode
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from resources.security.config import JWKS_URL

def get_public_key():
    """
    Busca a chave pública do endpoint JWKS e retorna em formato PEM.
    """
    try:
        response = requests.get(JWKS_URL, timeout=10)
        response.raise_for_status()
        jwks = response.json()

        if "keys" not in jwks or len(jwks["keys"]) == 0:
            raise ValueError("Nenhuma chave encontrada no JWKS")

        key = jwks["keys"][0]

        n = base64url_decode(key["n"].encode('utf-8'))
        e = base64url_decode(key["e"].encode('utf-8'))

        public_key = rsa.RSAPublicNumbers(
            e=int.from_bytes(e, byteorder="big"),
            n=int.from_bytes(n, byteorder="big")
        ).public_key()

        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem

    except requests.RequestException as e:
        raise RuntimeError(f"Erro ao buscar JWKS: {e}")
    except ValueError as e:
        raise RuntimeError(f"Erro ao processar JWKS: {e}")
