# PassAI Agent Guide

This file is the project map for Codex and other coding agents. Read it before
editing the repository. It defines the intended product scope, the modules that
matter, and the functions the system should expose.

## Product Scope

PassAI is a Brazil-only job search and CV adaptation system.

The goal is simple:

1. Know Leonardo's profile, experience, preferences, and deal-breakers.
2. Crawl Brazilian job sources for relevant opportunities.
3. Score and rank jobs by fit.
4. Save useful jobs to a pipeline/tracker.
5. Adapt Leonardo's CV for a selected job.
6. Export an ATS-friendly DOCX/PDF CV variant.

This project should be treated like a localized, Brazilian version of the
career-ops workflow: profile + portals + scanner + evaluation + tracker + CV
generation. The local reference implementation is:

`C:\Users\leonardo.ribeiro\Documents\career-ops-career-ops-v1.8.0`

## Explicit Non-Goals

Do not build, document, or expand these features:

- Real-time microphone transcription.
- System-audio transcription.
- Live AI chat over conversations.
- Screenshot capture.
- Screenshot or image analysis.
- Floating assistant overlays.
- Meeting/copilot behavior.

Some legacy files still exist for these features. Treat them as deprecated
unless the user explicitly asks to remove them or migrate code away from them.
New work should not depend on them.

Deprecated/legacy areas:

- `src/capture/`, `src/processing/`, `src/ui/`
- `backend/core/capture/`, `backend/core/processing/`, `backend/core/ui/`
- `backend/core/ai/vision_processor.py`
- WebSocket/audio/screenshot handlers in `backend/server.py`
- Audio/screenshot UI components in `frontend/renderer/components/`

## Target Market

All job discovery must be Brazil-focused.

Allowed target locations:

- Brasil / Brazil
- Remoto Brasil / Remote Brazil
- Hibrido or onsite in Brazilian cities
- Sao Paulo / SP
- Presidente Prudente / SP
- Other Brazilian cities or states when relevant

Reject or down-rank:

- US-only remote
- Europe-only remote
- Portugal-only remote unless explicitly open to Brazil
- LATAM roles that exclude Brazil
- Relocation-only jobs
- Jobs requiring local work authorization outside Brazil

## Brazilian Job Sources

Prioritize sources that are common in Brazil:

- Gupy
- LinkedIn Brasil
- Indeed Brasil
- Catho
- Glassdoor Brasil
- Programathor
- GeekHunter
- Trampos
- Remotar
- Revelo
- APInfo
- Empregos.com.br
- InfoJobs
- Company career pages with Brazil/Remote-Brazil filters

Existing scraper-related code:

- `backend/modules/jobs/scrapers/gupy.py`
- `backend/modules/jobs/scrapers/linkedin.py`
- `backend/modules/jobs/scrapers/indeed.py`
- `backend/modules/jobs/scrapers/catho.py`
- `backend/modules/jobs/scrapers/glassdoor.py`
- `backend/modules/jobs/scraper.py`
- `backend/modules/jobs/search_engine.py`

When adding new sources, prefer source-specific scraper classes registered in
the scraper registry rather than ad hoc logic inside API routes.

## Target Roles

Default matching should prioritize Leonardo's likely fit:

- Desenvolvedor Backend
- Desenvolvedor Full Stack / Fullstack
- Engenheiro de Software
- Java / Spring Boot
- C# / .NET
- Node.js
- React / Angular
- APIs REST
- Microsservicos
- Clean Architecture / DDD
- Mensageria: Kafka, RabbitMQ
- Bancos: Oracle, MySQL, MongoDB

Default exclusions:

- Estagio
- Junior, unless the user asks for it
- Comercial / Vendas
- Suporte puro
- Analista funcional sem desenvolvimento
- SAP/ABAP, Mainframe, COBOL
- Mobile-only iOS/Android
- Crypto/Web3

## Core Product Flows

### 1. Profile Setup

Source of truth:

- MongoDB `user_profiles`
- API: `backend/api/users/routes.py`
- Schemas: `backend/api/users/schemas.py`
- Guided profile logic: `backend/modules/profile/chat_agent.py` if retained

The system must know:

- Name, email, phone, LinkedIn, location.
- Target roles and seniority.
- Technologies and strongest proof points.
- Work preferences: remote/hybrid/onsite, CLT/PJ, salary range.
- Deal-breakers and preferred companies/domains.

### 2. Job Crawl

Main API surface:

- `POST /api/jobs/profiles`
- `GET /api/jobs/profiles`
- `POST /api/jobs/search/run`
- `GET /api/jobs/search/runs`
- `POST /api/jobs/scrape`
- `GET /api/jobs`
- `GET /api/jobs/ranked`

Important modules:

- `backend/modules/jobs/search_engine.py`
- `backend/modules/jobs/database.py`
- `backend/modules/jobs/models.py`
- `backend/modules/jobs/scraper.py`
- `backend/modules/jobs/scrapers/*`

The crawler should:

- Search only Brazilian-compatible jobs.
- Prefer recent jobs. Default freshness window is 14 days unless the user asks
  for a broader search.
- Do not keep jobs that clearly no longer accept applications. Detect and reject
  pages with phrases like "vaga encerrada", "não aceita mais candidaturas",
  "this job is no longer available", or equivalent closed/expired signals.
- Deduplicate by canonical URL and normalized title/company.
- Store raw source URL, title, company, location, modality, seniority, salary if present, requirements, and source.
- Keep crawl run stats and errors.
- Avoid mass-apply behavior. The system recommends and prepares; the human applies.

### 3. Job Fit Scoring

Important modules:

- `backend/modules/jobs/job_scorer.py`
- `backend/modules/jobs/enricher.py`
- `backend/modules/resume/ats_simulator.py`
- `backend/modules/resume/ats_detector.py`

Scoring should consider:

- Required stack match.
- Seniority match.
- Location and remote policy.
- Contract type and salary if known.
- Domain/company fit.
- Red flags: unpaid tests, vague job description, foreign-only location, seniority mismatch.

Output should be actionable:

- Overall score.
- Reasons to apply.
- Gaps/risks.
- Recommended next action.

### 4. Resume Adaptation

Main API surface:

- `POST /api/resume/jobs`
- `POST /api/resume/jobs/{job_id}/generate`
- `POST /api/resume/jobs/{job_id}/generate-more`
- `GET /api/resume/jobs/{job_id}/variants`
- `GET /api/resume/variants/{variant_id}`
- `GET /api/resume/variants/{variant_id}/download`
- `GET /api/resume/history`

Important modules:

- `backend/modules/resume/variant_generator.py`
- `backend/modules/resume/template_engine.py`
- `backend/modules/resume/job_extractor.py`
- `backend/modules/resume/ranker.py`
- `backend/modules/resume/llm_adapter.py`
- `layoutCV/layout.docx`

Resume adaptation rules:

- Never invent experience.
- Reorder and rephrase real experience to match the job.
- Inject relevant keywords naturally when backed by the profile.
- Preserve truthfulness and dates.
- Prefer PT-BR for Brazilian jobs unless the job description is in English.
- Keep output ATS-friendly and concise.
- Generated DOCX CVs must use `layoutCV/layout.docx` as the visual template.
  This template mirrors the reference PDF
  `Leonardo_valoes_novaes_ribeiro_Arquiteto de Software (1).pdf`. Do not use a
  generic DOCX layout for final CV exports.
- LinkedIn and GitHub in final CVs must be real clickable hyperlinks, not plain
  text. Display them as `linkedin.com/leonardo-valoes-ribeiro` and
  `github.com/leonvaloes`.
- Add visual spacing between professional experience blocks. The manually
  adjusted reference is `cv-sysmap-backend-pleno-java-enriquecido.docx`.
- Use correct Portuguese accents and cedilla in user-facing CVs and application
  messages. Do not strip accents for ASCII unless writing code/config files.
- Write CVs in an impersonal professional style, not first person and not
  biographical third person. Prefer phrases like "Atuacao atual na Security..."
  and "Experiencia em sistemas corporativos..." instead of "Atuo na..." or
  "Atualmente atua na...".

## AI Generation Architecture

The generation engine is Codex CLI.

Important files:

- `backend/core/llm/router.py`: backend `LLMRouter`; calls `codex exec`.
- `src/llm/router.py`: legacy monolithic copy of the same router.
- `backend/modules/resume/llm_adapter.py`: adapts `LLMRouter.generate()` for resume modules.
- `backend/api/users/routes.py`: AI profile extraction uses `llm_router.generate()`.

The router public API:

- `generate(prompt, temperature=..., max_tokens=..., seed=...) -> str`
- `generate_suggestion(conversation_history, current_intent, user_goal, screen_context=None) -> dict`
- `check_providers() -> {"codex": bool, "local": bool}`

Codex invocation pattern:

```powershell
codex exec --cd <repo-root> --sandbox read-only --output-last-message <temp-file> -
```

Environment overrides:

- `CODEX_COMMAND`
- `CODEX_MODEL`
- `CODEX_PROFILE`

Do not reintroduce OpenAI, Anthropic, Ollama, or other model-server calls for
generation.

## Repository Layout

- `backend/server.py`: FastAPI app. Contains legacy audio/screenshot code; new product work should focus on route modules.
- `backend/api/users/`: user profile API and CV text extraction.
- `backend/api/jobs/`: job CRUD, scraping, ranking, search profiles, crawl runs.
- `backend/api/resume/`: job-to-CV adaptation API.
- `backend/database/`: MongoDB connection and Pydantic/Mongo models.
- `backend/modules/jobs/`: crawler/search/scoring domain.
- `backend/modules/resume/`: CV adaptation, ATS scoring, DOCX generation.
- `backend/modules/profile/`: guided profile collection.
- `frontend/renderer/windows/jobs/`: job listing UI.
- `frontend/renderer/windows/job-search/`: job search/crawler UI.
- `frontend/renderer/windows/search-profiles/`: search profile UI.
- `frontend/renderer/windows/resume-generator/`: CV adaptation UI.
- `frontend/renderer/windows/user-management/`: profile management UI.
- `layoutCV/`: DOCX templates.
- `output/`: generated CV files.

## Data And Storage

- MongoDB database: `passai`.
- Default URI: `mongodb://localhost:27017/`.
- Docker service: `mongodb` in `docker-compose.yml`.
- Main Mongo wrapper: `backend/database/mongodb.py`.
- Jobs, variants, decisions, search profiles, crawl runs, and user profiles live in MongoDB.

## Commands

Install Python dependencies:

```powershell
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

Install frontend dependencies:

```powershell
cd frontend
npm install
```

Start MongoDB:

```powershell
docker compose up -d
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

Check Codex CLI:

```powershell
codex --version
codex exec --help
```

Python syntax check:

```powershell
python -m py_compile backend\core\llm\router.py backend\modules\jobs\search_engine.py backend\modules\resume\variant_generator.py
```

## Backend Endpoints To Preserve

Users:

- `GET /api/users`
- `POST /api/users`
- `GET /api/users/{user_id}`
- `PUT /api/users/{user_id}`
- `DELETE /api/users/{user_id}`
- `GET /api/users/active/current`
- `PUT /api/users/active/set`
- `POST /api/users/ai-extract`

Jobs:

- `POST /api/jobs`
- `POST /api/jobs/create`
- `POST /api/jobs/scrape`
- `GET /api/jobs`
- `GET /api/jobs/ranked`
- `GET /api/jobs/{job_id}`
- `DELETE /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/analyze`
- `POST /api/jobs/profiles`
- `GET /api/jobs/profiles`
- `GET /api/jobs/profiles/{profile_id}`
- `PUT /api/jobs/profiles/{profile_id}`
- `DELETE /api/jobs/profiles/{profile_id}`
- `POST /api/jobs/search/run`
- `GET /api/jobs/search/runs`
- `GET /api/jobs/search/runs/{run_id}`

Resume:

- `POST /api/resume/jobs`
- `GET /api/resume/jobs/{job_id}`
- `DELETE /api/resume/jobs/{job_id}`
- `POST /api/resume/jobs/{job_id}/generate`
- `POST /api/resume/jobs/{job_id}/generate-more`
- `GET /api/resume/jobs/{job_id}/variants`
- `GET /api/resume/variants/{variant_id}`
- `DELETE /api/resume/variants/{variant_id}`
- `GET /api/resume/variants/{variant_id}/download`
- `GET /api/resume/history`

Legacy endpoints may still exist, but should not guide new product design:

- `/ws`
- `/api/audio-devices`
- `/api/screenshot`
- `/api/screenshots`
- `/api/monitors`

## Coding Rules For Agents

- Build toward the Brazil-only job crawler and CV adaptation product.
- Do not add new audio, screenshot, meeting, or live chat behavior.
- Prefer extending `backend/modules/jobs` and `backend/modules/resume`.
- Keep `LLMRouter.generate()` stable because resume/job modules depend on it.
- Route AI generation through `backend/core/llm/router.py`.
- Use structured parsers/scraper classes instead of brittle route-level scraping.
- Keep Brazilian localization explicit: PT-BR labels, Brazilian portals, Brazilian location filters.
- Never auto-apply to jobs. The system finds, scores, prepares, and exports; Leonardo decides.
- Never invent CV facts. If a job requires something not in the profile, mark it as a gap.
- If changing API contracts, update matching frontend window code and this file.

## Career-Ops Reference Ideas To Borrow

Useful concepts from the local `career-ops` reference:

- User layer vs system layer.
- `cv.md` or Mongo user profile as source of truth.
- Portal configuration with positive/negative title filters.
- Deduped scan history.
- Job reports with score, rationale, risks, and next action.
- Human-in-the-loop workflow.
- CV generation that adapts to one job at a time.

Do not copy its non-Brazil defaults blindly. Replace global/US/EU portal logic
with Brazilian sources and Brazil-compatible location filters.
