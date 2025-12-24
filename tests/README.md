# Tests Directory

Testes unitários e de integração.

## Estrutura

```
tests/
├── test_basic.py            # Testes básicos
├── test_audio_capture.py    # Testes de captura de áudio
├── test_asr.py              # Testes de ASR
├── test_objection.py        # Testes de detecção de objeções
├── test_llm_router.py       # Testes do roteador LLM
├── integration/             # Testes de integração
│   └── test_pipeline.py
└── fixtures/                # Dados de teste
    ├── audio/
    └── images/
```

## Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Testes específicos
pytest tests/test_asr.py -v

# Com coverage
pytest tests/ --cov=src --cov-report=html

# Apenas integration tests
pytest tests/integration/ -v
```

## Benchmarks

```bash
python tests/benchmark.py
```
