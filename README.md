# PassAI

Projeto simplificado para duas funcionalidades:

- geracao de CV
- gerenciamento de usuarios

## Stack

- backend: FastAPI
- frontend: React + Vite
- armazenamento: JSON local
- saida de CV: DOCX

## Subir

```bash
./start.sh
```

Servicos:

- frontend: `http://127.0.0.1:5173`
- backend: `http://127.0.0.1:8000`

## Derrubar

```bash
./stop.sh
```

## Estrutura

- `backend/server.py`: API principal
- `backend/app_store.py`: persistencia local
- `backend/cv_service.py`: geracao e exportacao de CV
- `frontend/src/App.jsx`: interface principal

## Requisitos

- Python 3.11+
- Node.js 20+
- ambiente virtual em `venv/`

## Observacoes

- o projeto nao possui audio, transcricao, vision, chat, scraping ou filas
- o script `start.sh` grava PIDs em `.run/`
- o script `stop.sh` encerra backend e frontend usando esses PIDs
