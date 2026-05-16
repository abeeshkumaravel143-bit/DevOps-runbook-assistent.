# ⚙ OpsRunbook RAG
### RAG-Powered Intelligent System for Automated Incident Response Using LLaMA 2

---

## 🚀 Quick Start

### Option A — Docker (Recommended)

```bash
# 1. Copy and fill in your credentials
cp .env.example .env
# Edit .env: set GROQ_API_KEY, DB_PASSWORD, custom DB names

# 2. Run everything
docker-compose up --build

# 3. Open browser
http://localhost:8000
```

### Option B — Manual Setup

```bash
# ── Backend ──────────────────────────────────
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — add your GROQ_API_KEY and DB credentials

python main.py                    # starts on http://localhost:8000

# ── Frontend (separate terminal) ─────────────
cd frontend
npm install
npm run dev                       # dev server on http://localhost:5173

# OR build for production:
npm run build
# Then the FastAPI backend serves it automatically
```

---

## 🔐 First Login

1. Go to `http://localhost:8000`
2. Click **Register**
3. **No admin token needed** for the very first account — it automatically becomes admin
4. After that, only admins can register new users (via the Admin panel or using their session token)

---

## ⚙ Environment Variables (.env)

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Get free at [console.groq.com](https://console.groq.com) | required |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_USER` | DB username | `postgres` |
| `DB_PASSWORD` | **Your password** | required |
| `AUTH_DB_NAME` | Name for auth database | `opsrunbook_auth` |
| `APP_DB_NAME` | Name for app database | `opsrunbook_app` |

---

## 🏗 Architecture

```
User Browser
    │
    ▼
React SPA (Vite build)
    │  served by
    ▼
FastAPI (main.py)  ──▶  Groq API (LLaMA 2 / llama-3.1-8b-instant)
    │                        ▲
    ├──▶ RAG Pipeline ───────┘
    │       │
    │       ▼
    │    FAISS Index (vector search)
    │       │
    │       ▼
    │    runbooks.txt (chunked + embedded)
    │
    ├──▶ PostgreSQL AUTH DB  (users, sessions)
    └──▶ PostgreSQL APP DB   (audit_logs, chat_history, documents)
```

---

## 📋 Features

| Feature | Detail |
|---|---|
| 🧠 **RAG** | FAISS vector search → top-k chunks → LLaMA 2 answer |
| 📎 **File Upload** | PDF, Word, Excel, CSV — ask questions on your own docs |
| 🎤 **Voice I/O** | Web Speech API — speak questions, hear answers |
| 🔐 **Auth** | PBKDF2-hashed passwords, session tokens, role-based access |
| 📊 **Audit Logs** | Every query logged with latency, confidence, feedback |
| 📈 **Analytics** | Accuracy trend, latency trend, confidence distribution charts |
| 🏆 **Leaderboard** | Top answers ranked by confidence + user-verified helpful |
| ⬇ **CSV Export** | Download full audit log as CSV |
| 👥 **User Mgmt** | Admin can add/disable/delete users, change roles |
| 🐳 **Docker** | Multi-stage build, docker-compose with PostgreSQL |

---

## 👥 Roles

| Role | Chat | Audit Logs | Admin Panel |
|---|---|---|---|
| `admin` | ✅ | ✅ | ✅ |
| `devops` | ✅ | ✅ | ❌ |
| `viewer` | ✅ | ✅ | ❌ |

---

## 🏆 How Answer Correctness Works

1. **Confidence badge** on every AI message — `high`, `medium`, `low` based on FAISS retrieval score
2. **Source citations** show exactly which runbook section was used
3. **👍 / 👎 feedback** builds the accuracy trend in Analytics
4. **Leaderboard** surfaces the highest-confidence, user-verified answers as gold standard

---

## 📚 Runbook Knowledge Base

Built-in runbooks cover: Kubernetes, Docker, CI/CD pipelines, PostgreSQL, Linux, Nginx, Redis, MongoDB, RabbitMQ, Jenkins, GitHub Actions, Terraform, incident response playbooks, and more.

To add your own: use the **Admin → Documents** section or `POST /api/ingest`.

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/login` | Authenticate user |
| POST | `/api/register` | Register new user |
| POST | `/api/query` | Ask a DevOps question |
| POST | `/api/upload` | Upload file for analysis |
| POST | `/api/feedback` | Rate an answer helpful/not |
| GET | `/api/history` | Chat history for session |
| GET | `/api/audit-logs` | All audit log entries |
| GET | `/api/metrics` | Analytics + leaderboard data |
| GET | `/api/documents` | List ingested documents |
| POST | `/api/ingest` | Ingest new document (admin) |
| GET | `/api/users` | List all users (admin) |
| PUT | `/api/users/{id}/role` | Change user role (admin) |
| PUT | `/api/users/{id}/active` | Enable/disable user (admin) |
| DELETE | `/api/users/{id}` | Delete user (admin) |
| GET | `/health` | Health check |

---

## 🐳 Docker Commands

```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down

# Reset everything (including DB data)
docker-compose down -v
```

---

*Built on: FastAPI · React · FAISS · Groq API · LLaMA 2 · PostgreSQL · Docker*
