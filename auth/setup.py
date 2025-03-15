import os

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from requests.exceptions import SSLError, RequestException
from resources.security.config import KEYCLOAK_CLIENT_ID, KEYCLOAK_CLIENT_SECRET, TOKEN_URL


def setup_auth_client():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    client = BackendApplicationClient(client_id=KEYCLOAK_CLIENT_ID)
    oauth = OAuth2Session(client=client)

    try:
        token = oauth.fetch_token(token_url=TOKEN_URL, client_id=KEYCLOAK_CLIENT_ID, client_secret=KEYCLOAK_CLIENT_SECRET,
                                  verify="./kubernetes/certs/combined_certificates.pem")
        return oauth, token
    except SSLError as ssl_err:
        print("Erro SSL durante a tentativa de conexão:", ssl_err)
        raise ssl_err
    except RequestException as req_err:
        print("Erro na requisição:", req_err)
        raise req_err
