# Exemplo de Template DOCX com Placeholders

Este arquivo documenta como estruturar um template DOCX para uso com o PassAI.

## Opção 1: Placeholders Explícitos

Use marcadores `{{CAMPO}}` no template:

```
{{NOME}}
{{EMAIL}} | {{TELEFONE}} | {{LINKEDIN}}

RESUMO PROFISSIONAL
{{RESUMO}}

EXPERIÊNCIA PROFISSIONAL
{{EXPERIENCIA_1_EMPRESA}} - {{EXPERIENCIA_1_CARGO}}
{{EXPERIENCIA_1_PERIODO}}
• {{EXPERIENCIA_1_BULLET_1}}
• {{EXPERIENCIA_1_BULLET_2}}

EDUCAÇÃO
{{EDUCACAO_1_INSTITUICAO}}
{{EDUCACAO_1_CURSO}} - {{EDUCACAO_1_PERIODO}}

HABILIDADES
{{HABILIDADES}}
```

## Opção 2: Seções Predefinidas

Se o template não tem placeholders, o sistema detecta seções por headers:
- "Resumo Profissional" ou "Perfil"
- "Experiência Profissional"
- "Educação" ou "Formação"
- "Habilidades" ou "Skills"

E preenche os parágrafos subsequentes.

## Regras Importantes

1. **NÃO ALTERAR:**
   - Fonte (family, size, weight)
   - Cor de texto
   - Espaçamento (line-height, before/after)
   - Margens
   - Recuos
   - Quebras de página

2. **APENAS SUBSTITUIR:**
   - Texto dos placeholders
   - Conteúdo em áreas designadas

3. **Validação:**
   - Template deve ter exatamente 2 páginas
   - Após preenchimento, layout deve permanecer idêntico

## Exemplo de Conteúdo

```python
content = {
    "NOME": "Leonardo Valoes",
    "EMAIL": "leo@passai.dev",
    "TELEFONE": "(11) 99999-9999",
    "RESUMO": "Desenvolvedor Backend com 5+ anos de experiência...",
    "EXPERIENCIA_1_EMPRESA": "Tech Corp",
    "EXPERIENCIA_1_CARGO": "Senior Backend Developer",
    "EXPERIENCIA_1_PERIODO": "2020 - 2023",
    "EXPERIENCIA_1_BULLET_1": "Desenvolveu API RESTful com Django (Python) para 100k+ usuários",
    "EXPERIENCIA_1_BULLET_2": "Reduziu latência em 40% otimizando queries PostgreSQL"
}
```
