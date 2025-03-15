from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from resources.security.config import TOKEN_URL

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

api_key_header = APIKeyHeader(name="Authorization")
