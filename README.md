# ⚙️ DevOps Runbook Assistant

### RAG-Powered AI Assistant for DevOps Incident Response

An AI-powered assistant that helps DevOps and SRE teams quickly find troubleshooting solutions from operational runbooks.

Built with **FastAPI, React, FAISS, Groq (`llama-3.1-8b-instant`), and PostgreSQL**.

---

## 🚀 Quick Start

### 1. Prerequisites

* Python 3.11+
* Node.js 20+
* PostgreSQL 14+ running locally

### 2. Local Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/abeeshkumaravel143-bit/DevOps-Runbook-Assistant.git
cd DevOps-Runbook-Assistant
```

Copy the environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration, including:

```text
GROQ_API_KEY=your_api_key
DB_PASSWORD=your_password
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Build the frontend:

```bash
cd frontend
npm install
npm run build
cd ..
```

Start the application:

```bash
python main.py
```

Open:

```text
http://127.0.0.1:8000
```

Register your first account. The first registered account automatically becomes an administrator.

---

## 🐳 Docker

Docker is the recommended way to run the application.

Copy and configure the environment file:

```bash
cp .env.example .env
```

Build and start:

```bash
docker compose up --build
```

Open:

```text
http://localhost:8000
```

Stop the application:

```bash
docker compose down
```

Stop the application and remove database volumes:

```bash
docker compose down -v
```

> ⚠️ `docker compose down -v` removes database volumes and stored database data.

---

## 🏗️ Architecture

```text
                         Browser
                            │
                            ▼
                     React + Vite
                            │
                            ▼
                      FastAPI
                     (main.py)
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
     Auth                  RAG              Audit Engine
   (auth.py)             (rag.py)            (audit.py)
        │                   │
        ▼                   ├── FAISS Vector Store
   PostgreSQL              ├── Groq API
   Auth DB                 │   llama-3.1-8b-instant
                           └── runbooks.txt
                                │
                                ▼
                         Runbook Knowledge
                              Base
```

---

## 🧠 How RAG Works

The application uses **Retrieval-Augmented Generation (RAG)** to answer DevOps-related questions using the runbook knowledge base.

### Workflow

```text
User Question
      │
      ▼
Generate Query Embedding
      │
      ▼
FAISS Similarity Search
      │
      ▼
Retrieve Relevant Runbook Content
      │
      ▼
Groq LLM
(llama-3.1-8b-instant)
      │
      ▼
Generate Contextual Answer
      │
      ▼
User
```

This approach allows the assistant to retrieve relevant operational information before generating an answer.

---

## 📚 Runbook Knowledge Base

The project uses `runbooks.txt` as its knowledge base.

The file contains operational troubleshooting procedures and can be extended with additional runbooks.

Example topics can include:

* Kubernetes
* Docker
* Linux
* PostgreSQL
* Nginx
* CI/CD
* Incident response
* Infrastructure troubleshooting

---

## ➕ Adding Runbooks

Edit:

```text
runbooks.txt
```

Follow the existing runbook format:

```text
=============================================================================
RUNBOOK N: YOUR TITLE HERE

Tags: keyword1 keyword2 keyword3

=============================================================================

OVERVIEW:

...

STEP BY STEP PROCEDURE:

Step 1 - ...

Step 2 - ...
```

Restart the application after adding or modifying runbooks so they can be indexed.

---

## 🔐 Authentication & Security

The application includes:

* User registration and login
* Session-based authentication
* PBKDF2 password hashing
* Role-based access
* Protected administrative operations
* PostgreSQL-based authentication storage

The first registered account automatically receives the administrator role.

---

## 👥 User Roles

The application supports different user roles for controlling access to features such as administration and audit information.

### Admin

Administrators can manage users and access administrative features.

### DevOps

DevOps users can interact with the runbook assistant and access operational features.

### Viewer

Viewers can use the assistant to search and retrieve available runbook information.

---

## 📊 Audit & Logging

The application includes an audit engine for recording application activity and evaluating responses.

The audit system can track information such as:

* User queries
* Response information
* Response latency
* Correctness scoring
* Application activity

---

## 🔑 Environment Variables

Create a `.env` file from `.env.example`.

| Variable       | Description                  | Required |
| -------------- | ---------------------------- | :------: |
| `GROQ_API_KEY` | Groq API key                 |     ✅    |
| `DB_HOST`      | PostgreSQL host              |     ✅    |
| `DB_PORT`      | PostgreSQL port              |     ✅    |
| `DB_USER`      | PostgreSQL username          |     ✅    |
| `DB_PASSWORD`  | PostgreSQL password          |     ✅    |
| `AUTH_DB_NAME` | Authentication database name |     ✅    |
| `APP_DB_NAME`  | Application database name    |     ✅    |

> ⚠️ Never commit your `.env` file or API keys to GitHub.

---

## 📁 Project Structure

```text
DevOps-Runbook-Assistant/
│
├── main.py                # FastAPI application and routes
├── rag.py                 # RAG pipeline and FAISS integration
├── auth.py                # Authentication and session management
├── database.py            # PostgreSQL connections and schema
├── audit.py               # Audit logging and correctness scoring
├── runbooks.txt           # Runbook knowledge base
│
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── .env.example           # Environment variable template
│
└── frontend/
    └── src/
        └── pages/
            ├── Login.jsx
            ├── Chat.jsx
            ├── Logs.jsx
            └── Admin.jsx
```

---

## 🛠️ Technology Stack

| Layer            | Technology                               |
| ---------------- | ---------------------------------------- |
| Backend          | FastAPI + Python 3.11                    |
| Frontend         | React + Vite                             |
| AI Model         | `llama-3.1-8b-instant` via Groq          |
| Vector Search    | FAISS                                    |
| Database         | PostgreSQL                               |
| Authentication   | Session tokens + PBKDF2 password hashing |
| Containerization | Docker + Docker Compose                  |

---

## 🌐 Deployment

The application can be containerized and deployed to a cloud platform or VPS that supports Docker.

Possible deployment environments include:

* Railway
* Render
* DigitalOcean
* Hetzner
* Other Docker-compatible platforms

> Deployment configuration may vary depending on the hosting provider.

---

## 🎓 What I Learned

Building this project gave me practical experience with:

* Python backend development
* FastAPI
* REST APIs
* Retrieval-Augmented Generation
* FAISS vector search
* LLM integration
* Groq API
* PostgreSQL
* React and Vite
* Authentication and authorization
* Docker and Docker Compose
* Git and GitHub

---

## 👨‍💻 Author

**Abeesh K**

🐍 Python Developer | AI/ML Enthusiast

📍 Chennai, India

* GitHub: [Abeesh](https://github.com/abeeshkumaravel143-bit)
* LinkedIn: [Abeesh K](https://www.linkedin.com/in/abeesh-kumaravel-586b38292/)
* LeetCode: [Abeesh K](https://leetcode.com/u/abeeshkumaravel/)

📧 Email: [abeeshkumaravel143@gmail.com](mailto:abeeshkumaravel143@gmail.com)

---

⭐ If you found this project interesting, consider giving the repository a star.

**Built with:** Python · FastAPI · React · FAISS · Groq · PostgreSQL · Docker
