# AI Code Reviewer

Paste code → get **bugs**, **security issues**, and **improvements** powered by
**CodeBERT** (semantic analysis) + **Groq API** (LLM review) + **FastAPI** + **Streamlit**.

---

## Project structure

```
ai-code-reviewer/
├── backend/
│   ├── __init__.py            # makes backend a Python package
│   ├── main.py                # FastAPI app + CORS setup
│   ├── router.py              # POST /api/review endpoint
│   ├── codebert_analyzer.py   # language detection + embedding
│   └── groq_reviewer.py       # Groq LLM prompt + JSON parsing
├── frontend/
│   └── app.py                 # Streamlit UI
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> First run downloads the CodeBERT model (~500 MB) from HuggingFace Hub.

### 2. Set your Groq API key

Get a free key at https://console.groq.com, then:

```bash
export GROQ_API_KEY=your_key_here   # Linux / macOS
# or
set GROQ_API_KEY=your_key_here      # Windows CMD
```

### 3. Start the FastAPI backend

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 4. Start the Streamlit frontend (in a separate terminal)

```bash
streamlit run frontend/app.py
```

Open http://localhost:8501 in your browser.

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Liveness check |
| GET | /api/languages | List supported languages |
| POST | /api/review | Submit code for review |

### POST /api/review

Request body:
```json
{
  "code": "def foo():\n    pass",
  "language": "auto"
}
```

Response:
```json
{
  "language": "python",
  "bugs": ["foo() has no implementation and will silently do nothing."],
  "security_issues": [],
  "improvements": ["Add a docstring.", "Raise NotImplementedError if intentionally abstract."],
  "severity": "low",
  "summary": "The function is a stub. No security issues were found."
}
```

---

## Switching models

In `backend/groq_reviewer.py`, change the `model` argument:

| Model | Context | Best for |
|-------|---------|----------|
| `llama3-8b-8192` | 8 k tokens | Fast reviews, short files |
| `llama3-70b-8192` | 8 k tokens | Deeper analysis |
| `mixtral-8x7b-32768` | 32 k tokens | Long files (> 300 lines) |
