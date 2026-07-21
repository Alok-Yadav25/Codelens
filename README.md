# 🔍 CodeLens — AI Code Reviewer

## 🌐 Live Demo

**Try it now:** [codelens-alok-yadav-25.streamlit.app](https://codelens-alok-yadav-25.streamlit.app)

> Note: the backend runs on a free HuggingFace Space, so the first request may take 20-30 seconds to wake up.

## 📌 Overview

**CodeLens** is an AI-powered code review tool that combines **Microsoft CodeBERT** for semantic code understanding with **Groq's LLaMA 3** for natural language analysis. Paste any code snippet and get a structured review covering bugs, security vulnerabilities, performance improvements, and suggested fixes — all in seconds.

Built as a full-stack project with a **FastAPI** REST backend and a **Streamlit** frontend, serving structured reviews across 10 programming languages.

---

## ✨ Features

- 🐛 **Bug Detection** — finds logic errors with exact line numbers
- 🔒 **Security Analysis** — detects hardcoded secrets, SQL injection, unsafe patterns
- ✨ **Code Improvements** — suggestions for cleaner, more efficient code
- 🔧 **Suggested Fixes** — before/after code diff for every issue found
- 📊 **Performance Chart** — before vs after scores across 5 metrics (Plotly)
- 🌐 **10 Languages** — Python, JavaScript, TypeScript, Java, C++, Go, Rust, Swift, Ruby, PHP
- 🔍 **Auto Language Detection** — regex-based detection, no manual selection needed
- 📜 **Review History** — compare past reviews in the same session
- 🎨 **Dark UI** — clean Streamlit interface with gradient title and watermark

---

## 🏗️ Architecture

```
User Browser
     │
     ▼
┌─────────────────────┐
│  Streamlit Frontend  │  share.streamlit.io (free)
│  streamlit_app.py    │
└──────────┬──────────┘
           │ POST /api/review
           ▼
┌─────────────────────┐
│  FastAPI Backend     │  HuggingFace Spaces (free)
│  router.py           │
└──────┬──────┬───────┘
       │      │
       ▼      ▼
  CodeBERT  Groq API
  (HF API)  (LLaMA 3.1)
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Streamlit 1.35 | UI — code input, results display, charts |
| Backend | FastAPI 0.111 | REST API — request validation, routing |
| LLM | Groq API (LLaMA 3.1) | Natural language code review generation |
| Embeddings | CodeBERT (HuggingFace API) | Semantic code understanding, language detection |
| Charts | Plotly | Before/after performance visualization |
| Validation | Pydantic v2 | Request/response schema enforcement |
| Server | Uvicorn | ASGI server for FastAPI |

---

## 📁 Project Structure

```
codelens/
├── backend/
│   ├── __init__.py              # Package marker
│   ├── app.py                   # FastAPI app + CORS setup
│   ├── router.py                # POST /api/review endpoint + Pydantic schemas
│   ├── codebert_analyzer.py     # Language detection + HF API embeddings
│   └── groq_reviewer.py         # LLM prompt + JSON parsing
├── frontend/
│   ├── streamlit_app.py         # Full Streamlit UI
│   └── requirements.txt         # Frontend-specific dependencies
├── Dockerfile                   # Backend container (port 7860 for HF Spaces)
├── requirements.txt             # Backend dependencies
├── .gitignore                   # Excludes .env and secrets
└── README.md
```

---

## 🚀 Quick Start (Local)

### Prerequisites

- Python 3.11+
- [Groq API key](https://console.groq.com) (free)
- [HuggingFace token](https://huggingface.co/settings/tokens) (free)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/codelens.git
cd codelens
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install streamlit==1.35.0 plotly==5.22.0
```

### 4. Set environment variables

Create a `.env` file in the project root (never commit this):

```env
GROQ_API_KEY=gsk_your_key_here
HF_TOKEN=hf_your_token_here
BACKEND_URL=http://localhost:8000/api
ALLOWED_ORIGINS=http://localhost:8501
```

### 5. Run the backend

```bash
export $(grep -v '^#' .env | xargs)
uvicorn backend.app:app --reload --port 8000
```

### 6. Run the frontend (new terminal)

```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
streamlit run frontend/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🌐 Deployment (Free)

This project is deployed using two free services:

| Service | What it hosts | URL |
|---|---|---|
| HuggingFace Spaces | FastAPI backend | `https://YOUR_USERNAME-codelens-backend.hf.space` |
| Streamlit Community Cloud | Streamlit frontend | [codelens-alok-yadav-25.streamlit.app](https://codelens-alok-yadav-25.streamlit.app) |

### Deploy Backend → HuggingFace Spaces

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces) → SDK: **Docker**
2. Push this repo to the Space:
```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/codelens-backend
git push hf main
```
3. Add secrets in Space **Settings → Variables and secrets**:
```
GROQ_API_KEY  = gsk_your_key
HF_TOKEN      = hf_your_token
ALLOWED_ORIGINS = https://codelens-alok-yadav-25.streamlit.app
```

### Deploy Frontend → Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) → New app
2. Select this repo → `frontend/streamlit_app.py`
3. Add secret in **Advanced settings**:
```toml
BACKEND_URL = "https://YOUR_USERNAME-codelens-backend.hf.space/api"
```

---

## 📡 API Reference

Base URL: `http://localhost:8000` (local) or your HuggingFace Space URL

### `POST /api/review`

Request:
```json
{
  "code": "def divide(a, b):\n    return a / b",
  "language": "auto"
}
```

Response:
```json
{
  "language": "python",
  "bugs": [
    {"line": 2, "description": "No check for division by zero when b=0"}
  ],
  "security_issues": [],
  "improvements": ["Add input validation for parameters a and b"],
  "fixes": [
    {
      "original": "return a / b",
      "suggested": "return a / b if b != 0 else None"
    }
  ],
  "performance_scores": {
    "before": {"readability": 65, "security": 70, "performance": 60, "maintainability": 55, "best_practices": 60},
    "after":  {"readability": 85, "security": 90, "performance": 80, "maintainability": 80, "best_practices": 85}
  },
  "severity": "medium",
  "summary": "The function has a critical division by zero bug..."
}
```

### `GET /api/languages`

Returns the list of supported languages:
```json
{"languages": ["python", "javascript", "typescript", "java", "go", "ruby", "php", "cpp", "rust", "swift"]}
```

### `GET /health`

Liveness check for Docker/deployment health monitoring:
```json
{"status": "ok"}
```

---

## 🧪 Testing Accuracy

Run the language detection test (no backend needed):
```bash
python test_language_detection.py
```

Run the review quality test (backend must be running):
```bash
python test_review_quality.py
```

Expected results:
| Test | Target |
|---|---|
| Language detection | > 90% |
| Bug detection | > 75% |
| Security detection | > 70% |

---

## 🔑 Environment Variables

| Variable | Where | Description |
|---|---|---|
| `GROQ_API_KEY` | Backend | Groq API key from console.groq.com |
| `HF_TOKEN` | Backend | HuggingFace token for CodeBERT API |
| `ALLOWED_ORIGINS` | Backend | CORS allowed origins (your Streamlit URL) |
| `BACKEND_URL` | Frontend | Full URL to FastAPI backend `/api` |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "add your feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Alok Kumar Yadav**


Made with ❤️ by Alok Kumar Yadav
<img width="1440" height="820" alt="Screenshot 2026-06-07 at 4 49 12 PM" src="https://github.com/user-attachments/assets/667f3918-55e7-4b9d-ab1f-45dc2e88ab91" />
<img width="1434" height="764" alt="Screenshot 2026-06-07 at 4 49 38 PM" src="https://github.com/user-attachments/assets/92205679-c1e8-41de-bb1c-a6634bff8210" />
<img width="1440" height="817" alt="Screenshot 2026-06-07 at 4 49 54 PM" src="https://github.com/user-attachments/assets/3ba559e2-65ff-4704-9c36-c9a71041d742" />
