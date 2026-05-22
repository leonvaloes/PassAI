# Prompt Para Nova Sessão Codex

Use este arquivo quando abrir uma nova sessão do Codex neste repositório.

## Contexto do Projeto

Este projeto deixou de ser um assistente de áudio/chat/screenshot. O escopo
atual é um crawler brasileiro de vagas com adaptação de CV para Leonardo Valões
Novaes Ribeiro.

Leia primeiro:

1. `AGENTS.md`
2. `README.md`
3. `backend/scripts/populate_leonardo_profile.py`
4. Relatórios mais recentes em `reports/`
5. CVs recentes em `output/` e DOCX finais na raiz do projeto

## Prompt Base

```text
Você está no repositório PassAI.

Objetivo atual:
- Buscar vagas brasileiras recentes e abertas para Leonardo Valões Novaes Ribeiro.
- Priorizar Java, Spring Boot, backend/fullstack, APIs REST, microsserviços,
  Kafka/RabbitMQ, bancos SQL/NoSQL, fintech/pagamentos, sistemas corporativos,
  CI/CD, Docker, Kubernetes e AWS.
- Filtrar vagas que aceitam Brasil/remoto Brasil ou localidades brasileiras
  viáveis.
- Evitar vagas encerradas, antigas, sem botão/link de candidatura ou que não
  aceitam mais aplicações.
- Adaptar o CV para vagas escolhidas, usando fatos reais do perfil.

Regras obrigatórias:
- Não usar OpenAI API, Anthropic API, Ollama ou servidor externo de LLM.
- A geração deve passar pelo Codex CLI quando integrada ao sistema.
- Não reintroduzir áudio, microfone, system-audio, screenshot, visão ou chat ao
  vivo.
- Vagas devem ser totalmente brasileiras ou compatíveis com Brasil.
- CV final em DOCX deve usar `layoutCV/layout.docx`.
- LinkedIn e GitHub no CV devem ser links clicáveis:
  - linkedin.com/leonardo-valoes-ribeiro -> https://www.linkedin.com/in/leonardo-valoes-ribeiro/
  - github.com/leonvaloes -> https://github.com/leonvaloes
- Manter espaçamento visual entre cada experiência profissional.
- CV deve usar PT-BR com acentos e cedilha.
- Currículo deve ser escrito em estilo profissional impessoal:
  - usar "Atuação atual na...", "Experiência em..."
  - evitar "Atuo na..."
  - evitar "Atualmente atua na..."
- Nunca inventar experiência, data, tecnologia, métrica ou formação.
```

## Perfil Profissional Correto

Nome: Leonardo Valões Novaes Ribeiro  
Cidade: Presidente Prudente, SP  
Email: leonvaloesnovaes@gmail.com  
Telefone: (18) 99745-0885  
LinkedIn: linkedin.com/leonardo-valoes-ribeiro  
GitHub: github.com/leonvaloes  

Cronologia correta:

1. Security Segurança e Serviços: Maio/2022 a Maio/2024
2. iPag Pagamentos Digitais: Maio/2024 a Dezembro/2024
3. Security Segurança e Serviços: Janeiro/2025 até hoje

## Pontos Fortes Para CV

Security, segunda passagem:

- Participação ativa em duas auditorias, apoiando adequações técnicas e
  operacionais para garantir conformidade com os critérios avaliados pelos
  auditores.
- Desenvolvimento de fluxos corporativos usados por diferentes áreas da empresa,
  apoiando padronização de processos, redução de retrabalho e ganho operacional.
- Desenvolvimento do fluxo de desligamento em massa de colaboradores para
  encerramento de postos de serviço, integrando microsserviços, ERP Protheus e
  sistemas internos.
- Evolução de fluxos do ciclo de vida do colaborador: contratação, admissão,
  alteração de cargo, alteração salarial, aprovações, documentação e
  desligamento.

iPag:

- Processamento de pagamentos em lote, reduzindo rotinas de horas para minutos
  com execução assíncrona e concorrente.
- Cálculo e cobrança escalonada com regras configuráveis dinamicamente.
- Integração TEF.
- Correção de biblioteca open source de validação para uso interno.
- Autenticação 3DS no plugin iPag para Nuvemshop.
- Esteira de CI/CD.
- Configuração de filas e scheduler cron na AWS.
- Gateway com cartão, boleto, PIX, recorrência, links de pagamento e whitelabel.

Security, primeira passagem:

- Sistemas corporativos para ciclo de vida do colaborador.
- Alteração funcional/salarial com aprovação e integração com ERP Protheus.
- Rescisão contratual em lote.
- Efetivação de contratos com documentos, validação multiárea e notificações.
- Admissão com aprovações, documentos e integrações com ERP Protheus/Pandape.

## Vagas E Arquivos Recentes

Relatórios:

- `reports/2026-05-22-vagas-escolhidas.md`
- `reports/2026-05-22-vagas-poucas-aplicacoes.md`
- `reports/2026-05-22-vagas-brasil-novas.md`
- `reports/2026-05-21-vagas-brasil-novas.md`
- `reports/2026-05-20-vagas-brasil-shortlist.md`
- `reports/2026-05-20-mensagens-candidatura.md`

CVs finais recentes:

- `cv-sysmap-backend-pleno-java-final.docx`
- `cv-sysmap-backend-pleno-java-enriquecido.docx`
- `cv-sbm-fullstack-java-angular.docx`
- `cv-inter-developer-java.docx`
- `cv-senior-sistemas-java-folha-x.docx`
- `cv-bradesco-backend-java-pl-final.docx`

Markdown dos CVs:

- `output/cv-sysmap-backend-pleno-java.md`
- `output/cv-sbm-fullstack-java-angular.md`
- `output/cv-inter-developer-java.md`
- `output/cv-senior-sistemas-java-folha-x.md`
- `output/cv-bradesco-backend-java-pl.md`

## Como Gerar DOCX

Use:

```powershell
python scripts\markdown_cv_to_docx.py output\cv-sysmap-backend-pleno-java.md cv-sysmap-backend-pleno-java-final.docx
```

O script já deve:

- usar `layoutCV/layout.docx`;
- criar hyperlinks reais para LinkedIn e GitHub;
- adicionar espaçamento entre experiências;
- preservar acentos;
- evitar placeholders sobrando.

Validação rápida:

```powershell
python -c "from docx import Document; d=Document('cv-sysmap-backend-pleno-java-final.docx'); text='\n'.join(p.text for p in d.paragraphs); print('{{' in text); print([rel.target_ref for rel in d.part.rels.values() if 'hyperlink' in rel.reltype])"
```

## Branch Atual

Branch de trabalho criada para este conjunto:

`career-crawler-cv-codex`

## Checklist Para Próximas Sessões

- Conferir `git status --short` antes de editar.
- Buscar vagas novas somente se o usuário pedir.
- Se buscar vagas, usar fontes brasileiras e confirmar recência/status aberto.
- Para vagas escolhidas, criar CV em Markdown em `output/` e DOCX final na raiz.
- Atualizar relatório em `reports/`.
- Validar DOCX antes de entregar.
