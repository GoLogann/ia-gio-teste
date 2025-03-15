import yaml
import os


def load_config():
    env = os.getenv("ENV", "dev").lower()

    config_filename = f"config.{env}.yaml"
    config_path = os.path.join(os.path.dirname(__file__), config_filename)

    try:
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise RuntimeError(f"Arquivo de configuração '{config_filename}' não encontrado.")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Erro ao carregar o arquivo de configuração: {e}")


CONFIG = load_config()


def get_config(section: str, key: str = None):
    """
    Obtém um valor da configuração a partir de uma seção específica.

    Args:
        section (str): Nome da seção da configuração (ex: "db", "api", "security").
        key (str): Chave específica dentro da seção, se necessário.

    Returns:
        dict/str: A configuração completa da seção ou um valor específico dentro da seção.
    """
    section_config = CONFIG.get(section, {})
    if key:
        return section_config.get(key)
    return section_config
