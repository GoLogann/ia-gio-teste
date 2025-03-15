SUMMARY_TEMPLATE = """
# Resumo do Questionário de Avaliação

## Perguntas Gerais

### 1. Avaliação do Nível de Inovação
Pergunta: O seu projeto de produto/processos/sistemas pode ser considerado uma novidade para qual público?  
Enquadramento: Trata-se de um produto/processo/serviço cujo desenvolvimento de uma solução própria ainda é inédito em âmbito internacional.

Pergunta: Como você classifica as atividades realizadas pela sua empresa no desenvolvimento do projeto em questão?  
Enquadramento: No processo de desenvolvimento do produto/processo/sistema, a empresa atuou na elaboração de conceito, benchmarking, revisão de literatura científica e realizou ou coordenou a realização de testes/experimentos/ensaios em diferentes escalas e pesquisadores de dedicação exclusiva.

Pergunta: Como você classificaria o engajamento de sua empresa no desenvolvimento do projeto em questão?  
Enquadramento: A empresa tem uma política de inovação bem definida, com profissionais dedicados ao desenvolvimento de soluções e integração com o ambiente de inovação.

Pergunta: Como você avalia as novidades trazidas pelo seu projeto em comparação a outras alternativas disponíveis no mercado?
Enquadramento: Criação de um produto/processo ou sistema radicalmente distinto de quaisquer outros disponíveis no mercado, a ponto de levar a hábitos de consumo, culturas empresariais ou ambientes produtivos completamente inéditos, bem como levar ao declínio de quaisquer tecnologias concorrentes no momento.
                 
### 2. Modificadores de Nível de P&D
Pergunta: Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com Universidades?  
Enquadramento: Sim, em parceria com a Universidade de São Paulo (USP).

Pergunta: Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com ICT's?  
Enquadramento: Não.

Pergunta: Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com empresas parceiras?  
Enquadramento: Sim, em parceria com a XYZ Tecnologia.

### 3. Modificadores de Nível de Inovação
Pergunta: Esse projeto resultou em alguma forma de proteção de propriedade intelectual?  
Enquadramento: Sim, foi submetido um pedido de patente.

Pergunta: Esse projeto foi aprovado para captação de recursos junto à organização de Fomento ao PDI (FINEP/BNDES)?  
Enquadramento: Não.

Pergunta: Esse projeto foi submetido à LDB AC 2023?  
Enquadramento: Sim.

---

## Perguntas Específicas

### Área: TI_TECH
Pergunta: O seu projeto traz avanços em alguma das seguintes áreas?  
Enquadramento: IA Generativa.

### Área: ENERGIA
Pergunta: O seu projeto trouxe avanços em alguma das seguintes áreas?  
Enquadramento: Baterias com minerais estratégicos nacionais.

---

# Observações Adicionais
- Todas as respostas foram enquadradas corretamente conforme os critérios definidos.
- Não houve dúvidas ou inconsistências por parte do usuário.
- Na pergunta "Esse projeto resultou em alguma forma de proteção de propriedade intelectual?" ele tem uma sub pergunta 
pra quando o usuário responde sim para essa pergunta. Que é "Caso sim, esse projeto resultou em pedido de patente?". No
Campo enquadramento dessa pergunta adiciona a resposta que o usuário deu pra ela, se não, adicione somente não, se sim,
adicione sim e o complemento da pergunta que seria a pergunta se o projeto em questao resultou em algum pedido. Muita atenção
pra esse detalhe.
-Preencha cada enquadramento dando match nos enquadramentos existes no roteiro de perguntas com as respostas do usuario. 
Analise bem e veja qual enquadramento melhor se adequa ao que foi respondido.
"""
