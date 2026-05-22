# PassAI

PassAI is a Brazil-focused job crawler and CV adaptation system.

It is not a meeting assistant, audio copilot, screenshot analyzer, or live chat
overlay. The intended product is:

1. Crawl Brazilian job sources.
2. Find jobs that match Leonardo's profile.
3. Score and rank opportunities.
4. Store a practical job pipeline.
5. Adapt Leonardo's CV for a selected job.
6. Export an ATS-friendly CV variant.

The project uses **Codex CLI** for AI generation. It does not use OpenAI API,
Anthropic API, or Ollama for LLM generation.

## For Codex

Read [AGENTS.md](AGENTS.md) first. It is the operating guide for the current
scope: Brazilian crawler + job matching + CV adaptation.

## Main Features

- Brazilian job crawler/search profiles.
- Job scraping for sources such as Gupy, LinkedIn Brasil, Indeed Brasil, Catho,
  Glassdoor Brasil, and Brazilian company career pages.
- Fresh/open-job filtering: searches prioritize jobs from the last 14 days and
  reject postings that clearly no longer accept applications.
- Job scoring based on Leonardo's profile, stack, seniority, location, salary,
  and deal-breakers.
- User profile management and extraction from pasted CV/LinkedIn text.
- Resume/CV adaptation for a selected job.
- ATS scoring, DOCX generation, download, and history.
- Human-in-the-loop workflow: the system recommends and prepares; Leonardo
  decides where to apply.

## CV Writing Rules

- Final DOCX CVs must use `layoutCV/layout.docx`, which mirrors the reference
  PDF layout from `Leonardo_valoes_novaes_ribeiro_Arquiteto de Software (1).pdf`.
- LinkedIn and GitHub must be clickable links in final DOCX exports.
- Keep visual spacing between each professional experience block.
- CVs and application messages must use correct PT-BR accents and cedilla.
- CV text should use an impersonal professional style.
- Prefer "Atuação atual na Security..." or "Experiência em sistemas..." instead
  of first person ("Atuo na...") or biographical third person ("Atualmente atua
  na...").
- Never invent experience, dates, metrics, or technologies.

## Non-Goals

These are not part of the intended product:

- Real-time microphone transcription.
- System-audio transcription.
- AI chat over conversation context.
- Screenshot capture or screenshot analysis.
- Floating assistant overlay behavior.

Some legacy files for those features may still exist, but new work should not
expand them.

## Quick Start

Start MongoDB:

```powershell
docker compose up -d
```

Install dependencies:

```powershell
pip install -r requirements.txt
pip install -r backend/requirements.txt
cd frontend
npm install
```

Start backend:

```powershell
python backend\server.py
```

Start frontend:

```powershell
cd frontend
npm start
```

## Codex CLI

PassAI expects Codex CLI to be installed and authenticated:

```powershell
codex --version
codex exec --help
```

Optional environment variables:

```powershell
LLM_PROVIDER=codex
CODEX_MODEL=
CODEX_PROFILE=
```

If model/profile are empty, PassAI uses Codex CLI defaults.

## Important Paths

- `backend/api/jobs/`: job CRUD, scraping, search profiles, crawl runs.
- `backend/modules/jobs/`: crawler/search/scoring logic.
- `backend/api/resume/`: CV adaptation API.
- `backend/modules/resume/`: variant generation, ATS scoring, DOCX filling.
- `backend/api/users/`: user profile and CV extraction.
- `backend/database/`: MongoDB integration and models.
- `frontend/renderer/windows/job-search/`: crawler UI.
- `frontend/renderer/windows/jobs/`: job listing/ranking UI.
- `frontend/renderer/windows/resume-generator/`: CV adaptation UI.
- `layoutCV/`: DOCX templates.
- `output/`: generated CV files.
- `AGENTS.md`: complete Codex operating guide.

## Validation

Basic Python syntax check:

```powershell
python -m py_compile backend\core\llm\router.py backend\modules\jobs\search_engine.py backend\modules\resume\variant_generator.py
```

Frontend start check:

```powershell
cd frontend
npm start
```

## Reference

Use `C:\Users\leonardo.ribeiro\Documents\career-ops-career-ops-v1.8.0` as an
idea reference for the workflow: profile, portals, scan history, reports,
tracker, and CV generation. Adapt the concepts to Brazilian job sources and
Leonardo's profile.
