identifiers = {
    1: "GIO_CRIATIVA_ASSISTENTE",
    2: "FARMACOS_SAUDE",
    3: "INDUSTRIA",
    4: "ENERGIA",
    5: "TI_TECH",
    6: "SOCIOAMBIENTAL",
    7: "FINANCEIRA"
}

QUESTIONS = [
    "O seu projeto de produto/processos/sistemas pode ser considerado uma novidade para qual público?",
    "Como você classifica as atividades realizadas pela sua empresa no desenvolvimento do projeto em questão?",
    "Como você classificaria o engajamento de sua empresa no desenvolvimento do projeto em questão?",
    "Como você avalia as novidades trazidas pelo seu projeto em comparação a outras alternativas disponíveis no mercado?",
    "Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com Universidades?",
    "Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com ICT's?",
    "Esse projeto realizou experimentos/testes/ensaios/desenvolvimento em colaboração com empresas parceiras?",
    "Esse projeto resultou em alguma forma de proteção de propriedade intelectual? Caso sim, esse projeto resultou em pedido de patente?",
    "Esse projeto foi aprovado para captação de recursos junto à organização de Fomento ao PDI (FINEP/BNDES)?",
    "Esse projeto foi submetido à LDB AC 2023?"
]

questions_and_frameworks = """
Pergunta: O seu projeto de produto/processos/sistemas pode ser considerado uma novidade para qual público?
Enquadramentos:
    Traz uma novidade no contexto da empresa e adaptado para as necessidades da mesma, embora trate-se de um produto/processo/sistema amplamente disponível em empresas concorrentes.
    O produto/processo/sistema em questão já existe, mas está disponível apenas a poucos players do mercado, com margens para ajustes a contextos específicos.
    A solução proposta é uma novidade para todo um segmento específico do mercado.
    Trata-se de um produto/processo/serviço cujo desenvolvimento de uma solução própria ainda é inédito no Brasil.
    Trata-se de um produto/processo/serviço cujo desenvolvimento de uma solução própria ainda é inédito em âmbito internacional.

Pergunta: Como você classifica as atividades realizadas pela sua empresa no desenvolvimento do projeto em questão?
Enquadramentos:
    Foram realizados testes/experimentos/ensaios para validar uma solução ofertada por um fornecedor de tecnologia.
    Foram realizados testes/experimentos/ensaios e desenvolvimentos específicos para adequar uma solução ofertada por um fornecedor de tecnologia ao contexto da empresa e seu mercado.
    No processo de desenvolvimento do produto/processo/sistema, a empresa atuou na elaboração de conceito, benchmarking, revisão de literatura científica, mas não realizou testes/experimentos/ensaios.
    No processo de desenvolvimento do produto/processo/sistema, a empresa atuou na elaboração de conceito, benchmarking, revisão de literatura científica e realizou ou coordenou a realização de testes/experimentos/ensaios em diferentes escalas (ex. da bancada ao industrial, ou do MVP ao Software).
    No processo de desenvolvimento do produto/processo/sistema, a empresa atuou na elaboração de conceito, benchmarking, revisão de literatura científica e realizou ou coordenou a realização de testes/experimentos/ensaios em diferentes escalas e pesquisadores de dedicação exclusiva.

Pergunta: Como você classificaria o engajamento de sua empresa no desenvolvimento do projeto em questão?
Enquadramentos:
    A empresa atuou na definição das necessidades chave e procedeu com a busca e aquisição de soluções tecnológicas para as mesmas.
    A empresa definiu as necessidades chave e buscou parceiros estabelecidos no mercado para o desenvolvimento de solução específica.
    A empresa empregou colaboradores de forma parcial ao desenvolvimento de conceito e buscou parceiros, em especial inventores e startups, para o desenvolvimento propriamente dito da solução (produto/processo/sistema).
    A empresa empregou colaboradores de forma parcial ao desenvolvimento da solução (produto/processo/sistema) sem contar com um departamento de Pesquisa e Desenvolvimento estruturado.
    A empresa empregou colaboradores de um departamento de Pesquisa e Desenvolvimento próprio para desenvolvimento da solução (produto/processo/sistema).
    A empresa tem uma política de inovação bem definida, com profissionais dedicados ao desenvolvimento de soluções e integração com o ambiente de inovação.

Pergunta: Como você avalia as novidades trazidas pelo seu projeto em comparação a outras alternativas disponíveis no mercado?
Enquadramentos:
    Ajustes e calibrações que preservam as mesmas características funcionais e componentes de produtos/processos ou sistemas, embora incrementem produtividade/eficiência, ou reduzam custo.
    Adição de características/funcionalidades/módulos novos a um produto/processo ou sistema, de maneira a gerar melhoria significativa em seu desempenho ou percepção de valor.
    Criação de um produto/processo ou sistema composto por elementos bastante distintos ou com diferenças generalizadas para outras soluções disponíveis concorrentes ou aplicadas para as mesmas demandas.
    Criação de um produto/processo ou sistema radicalmente distinto de quaisquer outros disponíveis no mercado, a ponto de levar a hábitos de consumo, culturas empresariais ou ambientes produtivos completamente inéditos, bem como levar ao declínio de quaisquer tecnologias concorrentes no momento.

MODIFICADORES NIVEL DE P&D
                
Pergunta: Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com Universidades?
a. Se sim, quais?.
Pergunta: Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com ICT's?
a. Se sim, quais?.
Pergunta: Esse projeto realizou experimentos/testes/ensaios/desenvolvimento em colaboração com empresas parceiras?
a. Se sim, quais?.
                
MODIFICADORES NIVEL DE INOVAÇÃO
                
Pergunta: Esse projeto resultou em alguma forma de proteção de propriedade intelectual? Caso sim, esse projeto resultou em pedido de patente?.
Pergunta: Esse projeto foi aprovado para captação de recursos junto à organização de Fomento ao PDI (FINEP/BNDES)?
Pergunta: Esse projeto foi submetido à LDB AC 2023?
"""

def get_identifier_by_number(number):
    return identifiers.get(number, "Identificador não encontrado")