# Models Directory

Este diretório armazena modelos de ML locais.

## Estrutura

```
models/
├── objection_classifier/    # Modelo de classificação de objeções
│   ├── model.bin
│   ├── config.json
│   └── vocab.txt
├── whisper/                  # Modelos Whisper (se locais)
│   └── large-v3/
└── embeddings/               # Modelos de embeddings
    └── all-MiniLM-L6-v2/
```

## Download de Modelos

### Faster Whisper
Os modelos são baixados automaticamente pelo faster-whisper na primeira execução.

### Objection Classifier
```bash
# TODO: Implementar download automático
python scripts/download_models.py --model objection_classifier
```

### Embeddings
```bash
# Download via transformers
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

## Tamanhos Estimados

- Whisper large-v3: ~3GB
- Objection classifier: ~500MB
- Embeddings: ~80MB

**Total**: ~3.5GB
