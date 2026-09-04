# ⚙️ OpsRunbook RAG

### RAG-Powered Intelligent System for Automated Incident Response

An AI-powered DevOps assistant that helps DevOps and SRE teams quickly find solutions from operational runbooks.

The system uses **Retrieval-Augmented Generation (RAG)** to retrieve relevant runbook information and generate contextual answers with commands and source references.

---

## 🎯 Overview

During DevOps incidents, engineers often need to search through large amounts of documentation to find the correct troubleshooting steps.

**OpsRunbook RAG** simplifies this process by allowing users to ask questions in natural language.

For example:

> **How do I rollback a Kubernetes deployment?**

The application searches the runbook knowledge base, retrieves the most relevant information using vector similarity search, and generates an answer using an LLM.

### 🔄 High-Level Workflow

```text
User Question
      │
      ▼
React Frontend
      │
      ▼
FastAPI Backend
      │
      ▼
RAG Pipeline
      │
      ├── Generate Query Embedding
      │
      ├── Search FAISS Vector Index
      │
      └── Retrieve Relevant Runbook Chunks
      │
      ▼
LLM (Groq API)
      │
      ▼
Generated Answer + Sources
      │
      ▼
User
```

---

## 🚀 Key Features

| Feature                     | Description                                                                        |
| --------------------------- | ---------------------------------------------------------------------------------- |
| 🧠 **RAG Pipeline**         | Retrieves relevant information from operational runbooks before generating answers |
| 🔎 **Semantic Search**      | Uses FAISS vector search to find relevant document chunks                          |
| 🤖 **AI-Powered Answers**   | Generates contextual DevOps troubleshooting responses                              |
| 📄 **Document Upload**      | Supports PDF, Word, Excel and CSV documents                                        |
| 🎤 **Voice Input & Output** | Uses Web Speech API for voice interaction                                          |
| 🔐 **Authentication**       | Secure login with password hashing and session management                          |
| 👥 **Role-Based Access**    | Supports admin, DevOps and viewer roles                                            |
| 📊 **Audit Logging**        | Records queries, response latency, confidence and feedback                         |
| 📈 **Analytics Dashboard**  | Displays performance and response analytics                                        |
| 🏆 **Leaderboard**          | Highlights highly rated and verified answers                                       |
| ⬇️ **CSV Export**           | Allows audit data to be exported as CSV                                            |
| 🐳 **Docker Support**       | Containerized application with PostgreSQL                                          |

---

## 🛠️ Technology Stack

### Backend

* 🐍 Python
* ⚡ FastAPI
* 🔗 LangChain
* 🔎 FAISS
* 🤗 Hugging Face
* 🤖 Groq API
* 🗄️ PostgreSQL

### Frontend

* ⚛️ React
* ⚡ Vite
* 🎨 HTML / CSS
* 🎤 Web Speech API

### DevOps & Tools

* 🐳 Docker
* 🐙 Git & GitHub
* 💻 VS Code

---

## 🏗️ System Architecture

```text
                        ┌─────────────────────┐
                        │      User           │
                        │     Browser         │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   React + Vite      │
                        │     Frontend        │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │      FastAPI        │
                        │       Backend       │
                        └──────────┬──────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
                  ▼                ▼                ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │ RAG Pipeline │  │ PostgreSQL   │  │  Groq API    │
          │              │  │   Database   │  │     LLM      │
          └──────┬───────┘  └──────────────┘  └──────┬───────┘
                 │                                    │
                 ▼                                    │
          ┌──────────────┐                            │
          │    FAISS     │                            │
          │ Vector Index │                            │
          └──────┬───────┘                            │
                 │                                    │
                 ▼                                    │
          ┌──────────────┐                            │
          │   Runbook    │────────────────────────────┘
          │  Documents   │
          └──────────────┘
```

---

## 🧠 How RAG Works

The application follows a Retrieval-Augmented Generation pipeline.

### 1. Document Ingestion

Runbook documents are uploaded to the system.

```text
Documents
   ↓
Text Extraction
   ↓
Document Chunking
   ↓
Embeddings
   ↓
FAISS Vector Index
```

### 2. User Query

The user asks a DevOps-related question.

```text
"How do I restart a failed Kubernetes pod?"
```

### 3. Similarity Search

The question is converted into an embedding and compared against the FAISS vector index.

The most relevant document chunks are retrieved.

### 4. Answer Generation

The retrieved context is sent to the LLM through the Groq API.

```text
User Question
      +
Retrieved Context
      ↓
     LLM
      ↓
Contextual Answer
```

### 5. Response

The user receives the generated answer along with relevant source information.

---

## 📚 Runbook Knowledge Base

The system can work with operational documentation covering areas such as:

* Kubernetes
* Docker
* Linux
* PostgreSQL
* Nginx
* Redis
* MongoDB
* RabbitMQ
* Jenkins
* GitHub Actions
* CI/CD pipelines
* Terraform
* Incident response procedures

Custom documents can also be added through the application.

---

## 👥 User Roles

| Role     | Chat | Audit Logs | Admin Panel |
| -------- | :--: | :--------: | :---------: |
| `admin`  |   ✅  |      ✅     |      ✅      |
| `devops` |   ✅  |      ✅     |      ❌      |
| `viewer` |   ✅  |      ✅     |      ❌      |

### Admin

Administrators can:

* Manage users
* Change user roles
* Enable or disable accounts
* Delete users
* Ingest documents
* View audit information

### DevOps

DevOps users can:

* Ask technical questions
* Search the runbook knowledge base
* View their chat history
* Provide feedback on answers

### Viewer

Viewers can:

* Ask questions
* Search available runbooks
* View relevant responses

---

## 📊 Answer Evaluation

The application provides several mechanisms to evaluate generated answers.

### Confidence

Each response can display a confidence level based on the retrieved information.

```text
High
Medium
Low
```

### Source References

Retrieved runbook information can be displayed alongside the generated answer.

### User Feedback

Users can provide feedback using:

```text
👍 Helpful
👎 Not Helpful
```

This feedback can be used to monitor answer quality through the analytics dashboard.

---

## 🔐 Authentication & Security

The application includes:

* User registration and login
* Password hashing
* Session-based authentication
* Role-based authorization
* Protected administrative operations
* User account management

The first registered account is automatically assigned the administrator role.

---

## 📈 Analytics

The application provides analytics for monitoring system usage and response quality.

Available metrics include:

* Query history
* Response latency
* Confidence distribution
* User feedback
* Accuracy trends
* Answer leaderboard

Audit information can also be exported as CSV.

---

## 🔧 API Endpoints

| Method   | Endpoint                 | Description              |
| -------- | ------------------------ | ------------------------ |
| `POST`   | `/api/login`             | Authenticate a user      |
| `POST`   | `/api/register`          | Register a user          |
| `POST`   | `/api/query`             | Ask a DevOps question    |
| `POST`   | `/api/upload`            | Upload a document        |
| `POST`   | `/api/feedback`          | Submit answer feedback   |
| `GET`    | `/api/history`           | Retrieve chat history    |
| `GET`    | `/api/audit-logs`        | Retrieve audit logs      |
| `GET`    | `/api/metrics`           | Retrieve analytics data  |
| `GET`    | `/api/documents`         | List available documents |
| `POST`   | `/api/ingest`            | Ingest a document        |
| `GET`    | `/api/users`             | List users               |
| `PUT`    | `/api/users/{id}/role`   | Change user role         |
| `PUT`    | `/api/users/{id}/active` | Enable or disable user   |
| `DELETE` | `/api/users/{id}`        | Delete a user            |
| `GET`    | `/health`                | Application health check |

---

## 🚀 Quick Start

### Option 1 — Docker

Docker is the recommended way to run the application.

#### 1. Clone the repository

```bash
git clone https://github.com/abeeshkumaravel143-bit/DevOps-Runbook-Assistant.git

cd DevOps-Runbook-Assistant
```

#### 2. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then update the `.env` file with your configuration.

```text
GROQ_API_KEY=your_api_key
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
```

#### 3. Start the application

```bash
docker-compose up --build
```

#### 4. Open the application

```text
http://localhost:8000
```

---

## 💻 Manual Setup

### Backend

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

On Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
cp .env.example .env
```

Start the backend:

```bash
python main.py
```

The backend will run on:

```text
http://localhost:8000
```

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The development frontend will run on:

```text
http://localhost:5173
```

---

## 🔐 First Login

After starting the application:

1. Open `http://localhost:8000`
2. Click **Register**
3. Create the first account
4. The first account is automatically assigned the `admin` role
5. The administrator can then manage additional users

---

## ⚙️ Environment Variables

Create a `.env` file in the project root.

| Variable       | Description             | Default           |
| -------------- | ----------------------- | ----------------- |
| `GROQ_API_KEY` | API key for Groq        | Required          |
| `DB_HOST`      | PostgreSQL host         | `localhost`       |
| `DB_PORT`      | PostgreSQL port         | `5432`            |
| `DB_USER`      | PostgreSQL username     | `postgres`        |
| `DB_PASSWORD`  | PostgreSQL password     | Required          |
| `AUTH_DB_NAME` | Authentication database | `opsrunbook_auth` |
| `APP_DB_NAME`  | Application database    | `opsrunbook_app`  |

> ⚠️ Never commit your `.env` file or API keys to GitHub.

---

## 🐳 Docker Commands

### Build and start

```bash
docker-compose up --build -d
```

### View application logs

```bash
docker-compose logs -f app
```

### Stop containers

```bash
docker-compose down
```

### Reset containers and database volumes

```bash
docker-compose down -v
```

> ⚠️ The `-v` option removes database volumes and therefore deletes stored database data.

---

## 📁 Project Structure

```text
DevOps-Runbook-Assistant/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   └── runbooks/
│
├── app/
│   ├── ...
│
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

> The exact structure may vary depending on the current implementation.

---

## 🔮 Future Improvements

Planned improvements include:

* Improved retrieval accuracy
* More DevOps runbooks
* Advanced evaluation of generated answers
* Better document processing
* Improved authentication and authorization
* Deployment to a cloud platform
* Monitoring and observability
* Automated testing and CI/CD
* Improved UI/UX

---

## 🎓 What I Learned

Building this project helped me gain practical experience with:

* Python backend development
* FastAPI
* REST APIs
* Retrieval-Augmented Generation
* Vector databases and similarity search
* Document processing
* LLM integration
* PostgreSQL
* React and Vite
* Docker
* Authentication and authorization
* Git and GitHub

---

## 👨‍💻 Author

**Abeesh K**

🐍 Python Developer | AI/ML Enthusiast

📍 Chennai, India

* GitHub: [Abeesh](https://github.com/abeeshkumaravel143-bit)
* LinkedIn: [Abeesh K](https://www.linkedin.com/in/abeesh-kumaravel-586b38292/)
* LeetCode: [Abeesh K](https://leetcode.com/u/abeeshkumaravel/)
* Email: [abeeshkumaravel143@gmail.com](mailto:abeeshkumaravel143@gmail.com)

---

⭐ If you found this project interesting, consider giving the repository a star!

**Built with:** Python · FastAPI · React · FAISS · LangChain · PostgreSQL · Groq API · Docker
