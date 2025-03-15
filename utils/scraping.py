# Importando as bibliotecas necessárias
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Função para extrair o texto de uma página web


def extrair_texto(session, url):
    # Define os headers para simular um navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Faz a requisição HTTP
        response = session.get(url, headers=headers, verify=False, timeout=20)
        if response.status_code == 200:
            # Parseia o conteúdo HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extrai o texto
            textos = soup.get_text(separator=' ')
            # Limpa o texto removendo espaços extras
            textos_limpos = ' '.join(textos.split())
            return textos_limpos, response.status_code
        else:
            print(f"Erro ao acessar a página {url}: {response.status_code}")
            return '', response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return '', None

# Função para coletar os links de uma página


def coletar_sublinks(session, url_principal, soup):
    sublinks = set()
    # Encontra todos os links na página
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Converte links relativos em absolutos
        full_url = urljoin(url_principal, href)
        # Filtra apenas links do mesmo domínio
        if url_principal in full_url and urlparse(full_url).path != '':
            sublinks.add(full_url)
    return sublinks

# Função principal para fazer o crawling do site


def crawling_site(url_principal, profundidade_maxima=2, max_workers=5):
    # Inicializa conjuntos para controle
    links_processados = set()
    links_a_visitar = {url_principal}
    resultados = []

    # Configura a sessão HTTP com retry
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries,
                          pool_connections=10, pool_maxsize=10)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    # Usa ThreadPoolExecutor para processamento paralelo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        profundidade = 0
        while links_a_visitar and profundidade < profundidade_maxima:
            futuros = []
            novos_links = set()

            # Processa cada link não visitado
            for link in links_a_visitar:
                if link not in links_processados:
                    print(f"Enfileirando: {link}")
                    futuros.append(executor.submit(
                        extrair_texto, session, link))
                    links_processados.add(link)

            # Processa os resultados das threads
            for future in as_completed(futuros):
                texto, status_code = future.result()
                if texto:
                    resultados.append(texto)

                # Faz nova requisição para coletar links
                response = session.get(link, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }, verify=False, timeout=20)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    sublinks = coletar_sublinks(session, url_principal, soup)
                    novos_links.update(sublinks)

            # Atualiza links para próxima iteração
            links_a_visitar = novos_links
            profundidade += 1

    return resultados

if __name__ == '__main__':
    # URL inicial para começar o crawling
    url_principal = 'https://www.neoquimica.com.br/'

    # Configurações do crawling
    profundidade_maxima = 2
    max_workers = 5

    # Executa o crawling
    resultados = crawling_site(url_principal, profundidade_maxima, max_workers)
    print(str(resultados))