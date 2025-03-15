import yaml
import os


def load_config():
    env = os.getenv("ENV", "dev")  # Pega o valor da variável de ambiente 'ENV', padrão 'dev' se não estiver definida
    print(f"Loading config for environment: {env}")  # Adicione log para verificar
    file_path = f"resources/config.{env}.yaml"

    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)

    return config


# Carrega o arquivo de configuração de acordo com o ambiente
config = load_config()