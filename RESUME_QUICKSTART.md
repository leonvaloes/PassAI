# PassAI Resume Generator - Guia de Uso

## 🚀 Início Rápido

### 1. Setup

```bash
# Entrar na pasta do projeto
cd d:\p2\ai-copilot

# MongoDB
docker-compose up -d

# Ativar venv
.\venv\Scripts\activate

# Instalar dependências (dentro do venv)
pip install -r backend\requirements.txt
```

### 2. Executar Exemplo

```bash
python example_resume_generator.py
```

---

## 📖 Uso Programático

### Extrair Vaga

```python
from modules.resume.job_extractor import JobExtractor

extractor = JobExtractor(vision_processor, llm_router)

# De uma URL
job = extractor.extract({
    "type": "url",
    "content": "https://linkedin.com/jobs/12345"
})

# De texto colado
job = extractor.extract({
    "type": "text",
    "content": "Desenvolvedor Backend Python..."
})

# De screenshot
job = extractor.extract({
    "type": "screenshot",
    "content": "vaga_screenshot.png"
})
```

### Gerar Currículos

```python
from modules.resume.variant_generator import VariantGenerator

generator = VariantGenerator(llm, kb, ats_sim, config)

variants = generator.generate_variants(
    job=job,
    base_resume=meu_cv,
    template_path="layoutCV/layout.docx"
)

# Retorna quando:
# - 3 variantes com score ≥ 95, OU
# - Max 30 variantes, OU
# - Max 10 rounds, OU
# - Estagnação por 3 rounds
```

### Rankear e Escolher

```python
from modules.resume.ranker import Ranker

ranker = Ranker()
ranked = ranker.rank(variants, job)

# Top 3
top3 = ranked[:3]

for v in top3:
    print(f"Score: {v.ats_score} | Ranking: {v.ranking_score}")
```

### Preencher Template

```python
from modules.resume.template_engine import TemplateEngine

engine = TemplateEngine("layoutCV/layout.docx")

result = engine.fill_template(
    content=best_variant.content,
    output_path="output/cv_otimizado.docx"
)

if result['success']:
    print(f"✅ Pronto: {result['output_path']}")
```

---

## ⚙️ Configuração

Editar `backend/config/resume_config.yaml`:

```yaml
resume:
  max_variants: 30        # Máximo de variantes
  max_rounds: 10          # Máximo de rounds
  batch_size: 5           # Variantes por round
  approval_threshold: 95  # Score mínimo
  template_path: "layoutCV/layout.docx"
```

---

## 🎯 Currículo Base

Formato esperado:

```python
base_resume = {
    "nome": "Seu Nome",
    "email": "email@exemplo.com",
    "telefone": "(11) 99999-9999",
    "linkedin": "linkedin.com/seu-perfil",
    "github": "github.com/usuario",
    
    "resumo": "Profissional com X anos...",
    
    "experiencias": [
        {
            "empresa": "Empresa X",
            "cargo": "Desenvolvedor",
            "periodo": "2020 - 2023",
            "descricao": "Responsável por...",
            "bullets": [
                "Realizou X com Y",
                "Aumentou Z em 30%"
            ]
        }
    ],
    
    "habilidades": ["Python", "Django", "AWS"],
    
    "educacao": {
        "curso": "Ciência da Computação",
        "instituicao": "Universidade X",
        "periodo": "2016 - 2020"
    }
}
```

---

## 📊 Entradas Aceitas (Vaga)

1. **URL:** LinkedIn, Gupy, Glassdoor, Indeed
2. **Texto:** Cole o texto da vaga
3. **PDF:** Arquivo da vaga
4. **Screenshot:** Captura de tela da vaga

---

## 🎓 Aprendizado Contínuo

```python
from modules.resume.learning_engine import LearningEngine

learning = LearningEngine(ranker)

# Usuário escolheu uma variante
learning.record_decision(
    variant_id=variant.id,
    action="chosen",
    feedback="Ficou perfeito!"
)

# Ver insights
insights = learning.get_insights()
print(insights)
```

---

## 🐛 Debug

Se algo não funcionar:

1. **MongoDB rodando?**
   ```bash
   docker ps | grep mongo
   ```

2. **Ollama ativo?**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Logs:**
   - Backend imprime logs detalhados
   - Procurar por "ERROR" ou "❌"

---

## 📝 Template DOCX

Seu template está em: `layoutCV/layout.docx`

**Estrutura:**
- 36 parágrafos
- Seções: Cabeçalho, Resumo, Habilidades, Formação, Experiência
- Ver mapeamento completo em: `cv_template_mapping.md`

---

## 🎉 Pronto!

Sistema 100% funcional. Qualquer dúvida, consulte:
- `resume_generator_plan.md` - Plano completo
- `resume_generator_final.md` - Resumo final
- `passai_technical_documentation.md` - Docs técnicas
