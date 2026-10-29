# Personal AI Agent

An extensible personal assistant built with Python, OpenAI Responses API, FastAPI, Streamlit, and SQLite. It can chat, summarize PDF/TXT documents, retain session history, and use a small allowlisted set of local tools.

## Features

- **AI chat** powered by OpenAI's Responses API.
- **PDF and TXT ingestion** with PyMuPDF and UTF-8 decoding. Files are processed in memory and are not saved to disk by default.
- **SQLite memory** for per-session messages, tasks, and document summaries.
- **Tool calling** for basic arithmetic, task creation, task listing, and task completion.
- **Two interfaces**: Streamlit UI and a FastAPI JSON/multipart API.
- **Safety basics**: tool allowlist, restricted arithmetic AST evaluator, upload-size/text limits, environment-based secrets, and session-scoped task access.
- **Tests** for arithmetic restrictions, task isolation, and message persistence.

## Project structure

```text
personal-ai-agent/
├── app.py                  # Streamlit UI
├── app/
│   ├── agent.py             # OpenAI Responses API and tool loop
│   ├── config.py            # Environment configuration
│   ├── document_reader.py   # PDF/TXT extraction
│   ├── main.py              # FastAPI routes
│   └── tools.py             # Allowlisted tools
├── database/db.py           # SQLite persistence
├── tests/test_tools.py
├── data/uploads/.gitkeep
├── .env.example
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.11+ recommended
- An OpenAI API key and API access to the configured model
- Internet access for model requests

## Setup

### macOS / Linux

```bash
git clone https://github.com/YOUR_USERNAME/personal-ai-agent.git
cd personal-ai-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY` to your own key. Never commit `.env` or paste API keys into source files.

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Run the Streamlit app

From the repository root:

```bash
streamlit run app.py
```

## Run the FastAPI backend

In a separate terminal with the same virtual environment activated:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. `GET /health` checks that the service is running and reports whether an API key is configured (never returns the key).

### API examples

Chat:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"demo-session","message":"Calculate (1200 * 3) / 4"}'
```

Upload and summarize a document:

```bash
curl -X POST http://127.0.0.1:8000/documents \
  -F 'session_id=demo-session' \
  -F 'file=@report.pdf'
```

List tasks:

```bash
curl http://127.0.0.1:8000/tasks/demo-session
```

## Run tests

```bash
pytest -q
```

Tests do not need a real OpenAI API key.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | empty | Your OpenAI API key; required for AI requests |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Model name available to your API account |
| `DATABASE_PATH` | `data/agent.db` | SQLite database path |
| `MAX_UPLOAD_MB` | `15` | Maximum uploaded file size |
| `MAX_DOCUMENT_CHARS` | `50000` | Maximum extracted document characters sent to the model |
| `AGENT_MAX_TOOL_CALLS` | `5` | Maximum tool-call rounds per request |

## Security and limitations

- This is a portfolio-ready **starter**, not a hardened multi-user production service.
- Do not expose the API publicly without authentication, rate limiting, HTTPS, and stronger session ownership. Session IDs are identifiers, not authentication.
- Never allow arbitrary shell execution, unrestricted SQL, or arbitrary filesystem access from model tool calls. This project intentionally does not expose those.
- Uploaded text is treated as untrusted content, but prompt injection cannot be eliminated perfectly. Review important outputs.
- OCR is not included; image-only/scanned PDFs may have no extractable text.
- Chat calls use an external AI provider; avoid uploading sensitive documents unless you are authorized to do so.
- The app does not send emails, make purchases, or perform actions beyond the explicitly implemented local tools.
- Tool actions requested by the model should be reviewed before using this app for consequential workflows.

## GitHub upload

Create an empty GitHub repository named `personal-ai-agent`, then from this folder run:

```bash
git init
git add .
git commit -m "Initial Personal AI Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/personal-ai-agent.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Check `.gitignore` before committing and ensure `.env` is not staged.

## License

Add a license file if you plan to publish or reuse this project under explicit terms.
