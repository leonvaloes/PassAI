
import asyncio
import logging
import sys
import os

# Setup paths
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from modules.resume.job_extractor import JobExtractor
from modules.resume.llm_adapter import create_llm_for_resume
from database.mongodb import get_mongodb

# Config logging
logging.basicConfig(level=logging.DEBUG) # DEBUG level to see adapter logs
logger = logging.getLogger(__name__)

JOB_TEXT = """
Luizalabs
 4.6
DESENVOLVEDOR(A) JAVA SR OPEN BANKING - TRIBO BAAS - FINTECH MAGALU
... (truncated for brevity, using same text as before) ...
"""

async def run_test():
    try:
        print("Initializing LLM Adapter (Production Mode)...")
        # THIS IS WHAT PRODUCTION USES:
        llm_router = create_llm_for_resume()
        
        print(f"Adapter Type: {type(llm_router)}")
        print(f"Has .llm attribute? {hasattr(llm_router, 'llm')}")
        
        print("Initializing JobExtractor...")
        # Production passes the adapter as llm_router
        extractor = JobExtractor(llm_router=llm_router)
        
        print("Extracting job data...")
        job = extractor.extract({
            "type": "text",
            "content": JOB_TEXT
        })
        
        print("\n=== EXTRACTED DATA ===")
        print(f"Title: {job.cargo}")
        print(f"Company: {job.empresa}")
        print(f"Skills: {job.requisitos_tecnicos}")
        print(f"Soft Skills: {job.requisitos_comportamentais}")
        print("======================\n")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)

if __name__ == "__main__":
    # Add the text back because I truncated it for the tool call but need it for the test
    FULL_TEXT = """
Luizalabs
 4.6
DESENVOLVEDOR(A) JAVA SR OPEN BANKING - TRIBO BAAS - FINTECH MAGALU
DESENVOLVEDOR(A) JAVA SR OPEN BANKING - TRIBO BAAS - FINTECH MAGALU
Sênior, Remoto

Como é o ambiente de trabalho?
Somos a Fintech Magalu, a vertical de produtos e serviços financeiros do grupo Magazine Luiza. Como parte de um dos pilares estratégicos do Magalu, nosso ecossistema possui tecnologias de meios de pagamento desenvolvidas por um time incrível.

Sim! Temos a cultura de desenvolver a tecnologia de todos os nossos produtos e gostamos do desafio de trabalhar em larga escala, cuidando para que os clientes tenham uma experiência excepcional conosco.

Ao longo dos últimos anos crescemos de forma exponencial e nos tornamos uma das maiores empresas do segmento. Desenvolvemos soluções para contas digitais, gestão de recebíveis, split de pagamentos, saques e transferências, pagamentos corporativos, adquirência, pix, cartão de crédito, crédito, e muito mais. Contamos com milhões de clientes presentes em todo o território nacional e estamos sempre buscando formas inovadoras de criar nossos produtos.

Nosso propósito é digitalizar empresas, especialmente empreendedores brasileiros, além de promover a inclusão de pessoas no sistema financeiro através das nossas plataformas!

Estamos procurando alguém que saiba lidar com desafios diários e com capacidade de trabalhar em equipe. Que some ao time, faça as coisas acontecerem e esteja preparado para as mudanças tecnológicas constantes e demandas próprias e desafiadoras.

Queremos construir produtos cada vez melhores - inovadores, rentáveis, escaláveis e com os quais as pessoas adoram trabalhar. Buscamos oferecer o melhor com o que temos. Gostamos de pessoas e nos ajudamos mutuamente. Se você é apaixonado(a) pelo o que faz, estuda sempre, forma talentos e trabalha em equipe essa vaga é para você!

Diversidade
O Magalu promove a diversidade.

Aqui você é bem-vindx em todas as vagas independentemente de gênero, orientação sexual, raça, etnia ou deficiência.

Responsabilidades da Oportunidade
Principais atividades:

Desenvolvimento de novas funcionalidades;

Participar de discussões técnicas com o time;

Fazer code review;

Participar das cerimônias (review, retrospectiva, planning, refinamentos), estimando esforço, ajudando a discutir sobre os projetos, levantando dúvidas, impactos, sugestões, etc

Criação de testes de unidade;

Alinhamento contínuo com os QAs do time;

Participar de comitê de GMUD;

Ser responsável pelas features desde o desenvolvimento até a entrega em produção

Requisitos
Requisitos:

experiência com linguagem de programação Java;

experiência com Spring Cloud e Spring Boot;

nosql e mysql;

arquitetura de microserviços;

mensageria (AWS SQS, RabbitMQ);

conhecimento com docker;

testes de unidade;

SOLID, patterns;

Git e metodologia ágeis;

Desejáveis:

conhecimento de ci/cd do gitlab;

conhecimento de kubernetes;

quarkus;

Benefícios

Assist. Médica
Assist. Odontológica
Desconto em Produtos
Poss. Horário Flexível
Seguro de Vida
Vale-Alimentação
Vale-Transporte
Missão da Organização
Nossa missão é criar  produtos e serviços, oferecendo ao cliente final mais benefícios e uma melhor experiência de compra.

Sobre a Organização
A tecnologia sempre esteve presente no Magalu, mas foi a partir de 2011 que que a nossa laboratório de tecnologia. Luizalabs, como é conhecida nossa área de inovação, foi responsável pelo grande case de transformação digital pela qual passamos e agora está crescendo para digitalizar o Brasil e levar a muitos o que é privilégio de poucos. Estamos investindo cada vez mais para criar soluções relevantes para todo o ecossistema da marca e transformar a experiência de consumo.
Hoje, só em tecnologia nós temos cerca de 1.500 profissionais divididos nos 5 escritórios ou trabalhando full time remoto nas áreas de desenvolvimento de software, Produto, Data Science e Machine Learning, UX e UI e agilidade.
    """
    
    # Override content
    JOB_TEXT = FULL_TEXT
    asyncio.run(run_test())
