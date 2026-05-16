"""
DevOps Runbook Assistant - RAG Pipeline with FAISS
Fixed: All Pylance/FAISS errors resolved
Loads runbooks from runbooks.txt automatically
"""

import os, time, json, httpx, hashlib, pickle
import numpy as np
from typing import List, Dict, Optional
from dotenv import load_dotenv
from database import insert_document

load_dotenv()

GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "gsk_7pYp47gt1f..........s1hpmDy9CoGbQ2jHXB")
GROQ_URL         = "https://api.groq.com/openai/v1/chat/completions"
MODEL            = "llama-3.1-8b-instant"
FAISS_INDEX_PATH = "faiss_index.pkl"

# ── Import FAISS safely (fixes Pylance reportPossiblyUnbound error) ───────
faiss_lib = None
FAISS_AVAILABLE = False
try:
    import faiss as faiss_lib
    FAISS_AVAILABLE = True
    print("✅ FAISS loaded successfully")
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not available — using numpy fallback")

# ── System Prompt ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert DevOps and SRE assistant.

STRICT RULES:
1. ALWAYS give a helpful, detailed, accurate answer — NEVER refuse
2. If runbook context is provided, use it as primary source and cite it
3. If file content is provided, read it and answer from it directly
4. If no context matches, answer from expert DevOps knowledge
5. Format with numbered steps for procedural questions
6. Include actual commands, file paths, parameters
7. Quote exact figures, numbers, dates from documents when asked
8. NEVER say "the document does not contain" — look harder

RESPONSE FORMAT — return ONLY valid JSON:
{
  "answer": "Detailed answer. Use \\n for new lines.",
  "sources": ["source name if used"],
  "confidence": "high"
}"""

# ── DevOps keyword vocabulary ─────────────────────────────────────────────
KEYWORDS = [
    "kubernetes","kubectl","pod","deployment","rollback","service",
    "ingress","namespace","helm","container","docker","image",
    "registry","cluster","node","cicd","jenkins","pipeline",
    "build","deploy","git","github","commit","branch","merge",
    "release","artifact","cache","test","lint","stage","production",
    "database","mysql","postgres","postgresql","mongodb","migration",
    "backup","restore","query","schema","index","replica","snapshot",
    "transaction","server","linux","ubuntu","nginx","apache","ssl",
    "tls","certificate","https","firewall","network","vpc","load",
    "balancer","proxy","dns","domain","cpu","memory","ram","disk",
    "storage","log","monitor","alert","metric","grafana","prometheus",
    "pagerduty","incident","outage","performance","latency","restart",
    "stop","start","scale","health","check","verify","debug","fix",
    "error","crash","timeout","connection","port","config","env",
    "variable","security","auth","token","password","secret","key",
    "encrypt","permission","runbook","procedure","recovery","cleanup",
]
VECTOR_DIM = len(KEYWORDS)


class FAISSVectorStore:
    """
    FAISS-based vector store.
    Falls back to numpy cosine similarity if FAISS not installed.
    """

    def __init__(self):
        self.metadata: List[Dict] = []
        self.np_vectors: List[np.ndarray] = []

        if FAISS_AVAILABLE and faiss_lib is not None:
            self.index = faiss_lib.IndexFlatIP(VECTOR_DIM)
        else:
            self.index = None

    def add(self, vector: np.ndarray, meta: Dict) -> None:
        vec = vector.reshape(1, -1).astype(np.float32)
        if FAISS_AVAILABLE and self.index is not None:
            self.index.add(vec)
        else:
            self.np_vectors.append(vector.copy())
        self.metadata.append(meta)

    def search(self, query: np.ndarray, k: int = 3) -> List[Dict]:
        if not self.metadata:
            return []

        q = query.reshape(1, -1).astype(np.float32)

        # ── FAISS search ──────────────────────────────────────────────────
        if FAISS_AVAILABLE and self.index is not None and faiss_lib is not None:
            total = int(self.index.ntotal)
            if total == 0:
                return []
            actual_k = min(k, total)

            # allocate output arrays manually (fixes Pylance argument errors)
            out_distances = np.empty((1, actual_k), dtype=np.float32)
            out_labels    = np.empty((1, actual_k), dtype=np.int64)
            self.index.search(q, actual_k, out_distances, out_labels)

            results: List[Dict] = []
            for score, idx in zip(out_distances[0], out_labels[0]):
                int_idx = int(idx)
                if int_idx >= 0 and int_idx < len(self.metadata) and float(score) > 0.001:
                    item = dict(self.metadata[int_idx])
                    item["score"] = float(score)
                    results.append(item)
            return results

        # ── Numpy fallback ────────────────────────────────────────────────
        if not self.np_vectors:
            return []
        vecs   = np.array(self.np_vectors, dtype=np.float32)
        scores = (vecs @ query.astype(np.float32)).tolist()
        top_k  = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for idx in top_k:
            if scores[idx] > 0.001:
                item = dict(self.metadata[idx])
                item["score"] = float(scores[idx])
                results.append(item)
        return results

    def reset(self) -> None:
        self.metadata   = []
        self.np_vectors = []
        if FAISS_AVAILABLE and faiss_lib is not None:
            self.index = faiss_lib.IndexFlatIP(VECTOR_DIM)
        else:
            self.index = None

    def save(self, path: str) -> None:
        try:
            data = {"metadata": self.metadata, "np_vectors": self.np_vectors}
            if FAISS_AVAILABLE and self.index is not None and faiss_lib is not None:
                faiss_lib.write_index(self.index, path + ".faiss")
            with open(path, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"FAISS save warning: {e}")

    def load(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.metadata   = data.get("metadata",   [])
            self.np_vectors = data.get("np_vectors", [])
            if FAISS_AVAILABLE and faiss_lib is not None:
                fpath = path + ".faiss"
                if os.path.exists(fpath):
                    self.index = faiss_lib.read_index(fpath)
            return bool(self.metadata)
        except Exception:
            return False


class RAGPipeline:
    """
    Full RAG pipeline:
    ingest → chunk(512) → embed → FAISS → retrieve(top3) → prompt → LLM → answer
    """

    def __init__(self):
        self.store = FAISSVectorStore()

        if os.path.exists(FAISS_INDEX_PATH):
            loaded = self.store.load(FAISS_INDEX_PATH)
            if loaded:
                n = len(set(m["doc_id"] for m in self.store.metadata))
                print(f"✅ FAISS index loaded: {len(self.store.metadata)} chunks from {n} docs")
                return

        # First run — build index from runbooks.txt + defaults
        print("Building FAISS index for first time...")
        self._load_from_file()
        self._load_defaults()
        print(f"✅ RAG ready: {len(self.store.metadata)} total chunks")

    # ── Ingest a document ─────────────────────────────────────────────────
    def ingest(self, title: str, content: str, tags: str = "") -> str:
        doc_id = "rb-" + hashlib.md5(title.encode()).hexdigest()[:6]
        chunks = self._chunk(content, size=512)
        for i, chunk in enumerate(chunks):
            embedding = self._embed(f"{title} {tags} {chunk}")
            self.store.add(embedding, {
                "doc_id":  doc_id,
                "title":   title,
                "content": chunk,
                "tags":    tags,
                "chunk_i": i,
            })
        try:
            insert_document(doc_id, title, content, tags, len(chunks))
        except Exception as e:
            print(f"DB insert warning: {e}")
        self.store.save(FAISS_INDEX_PATH)
        return doc_id

    # ── Retrieve top-k chunks ─────────────────────────────────────────────
    def retrieve(self, query: str, k: int = 3) -> List[Dict]:
        q_emb   = self._embed(query)
        results = self.store.search(q_emb, k=k)
        if results:
            print(f"Retrieved {len(results)} chunks, top={results[0].get('score',0):.4f}")
        return results

    # ── Main query entry point ────────────────────────────────────────────
    async def query(self,
                    question: str,
                    file_content: Optional[str] = None,
                    file_name:    Optional[str] = None) -> Dict:
        start = time.time()

        # ── FILE MODE ─────────────────────────────────────────────────────
        if file_content and file_name:
            if file_content.startswith("PDF_SCANNED:"):
                return {
                    "answer": (
                        "This PDF is a scanned image — it contains pictures of text.\n\n"
                        "To fix:\n"
                        "Option 1: Right-click PDF → Open with Microsoft Word → Save as .docx\n"
                        "Option 2: Upload to Google Drive → Open with Google Docs → Download as .docx"
                    ),
                    "sources": [], "confidence": "high",
                    "latency_ms": 0, "retrieved_chunks": 0,
                }

            relevant = self._smart_chunk_file(file_content, question)
            prompt   = (
                f"You are reading a document: '{file_name}'\n\n"
                f"DOCUMENT CONTENT:\n{relevant}\n\n"
                f"USER QUESTION: {question}\n\n"
                f"The answer IS in the document. State it directly with exact numbers."
            )
            retrieved: List[Dict] = []

        # ── RAG MODE ──────────────────────────────────────────────────────
        else:
            retrieved = self.retrieve(question, k=3)
            if retrieved:
                context = "\n\n".join(
                    f"=== {r['title']} ===\n{r['content']}"
                    for r in retrieved
                )
                prompt = (
                    f"RUNBOOK CONTEXT:\n{context}\n\n"
                    f"QUESTION: {question}\n\n"
                    f"Answer with exact commands and steps from the context above."
                )
            else:
                prompt = (
                    f"QUESTION: {question}\n\n"
                    f"No runbook found. Answer from expert DevOps knowledge."
                )

        # ── Call LLM ──────────────────────────────────────────────────────
        raw = await self._llm(prompt)

        # ── Parse response ────────────────────────────────────────────────
        try:
            clean = raw.strip()
            si    = clean.find("{")
            ei    = clean.rfind("}") + 1
            if si != -1 and ei > si:
                clean = clean[si:ei]
            parsed = json.loads(clean)
            if not parsed.get("answer"):
                parsed["answer"] = raw
        except Exception:
            parsed = {
                "answer":     raw or "Sorry, please try again.",
                "sources":    [],
                "confidence": "medium",
            }

        if "sources" not in parsed:
            parsed["sources"] = (
                [r["title"] for r in retrieved] if retrieved
                else ([file_name] if file_name else [])
            )
        if "confidence" not in parsed:
            parsed["confidence"] = "high"

        if isinstance(parsed.get("answer"), str):
            parsed["answer"] = parsed["answer"].replace("\\n", "\n")

        parsed["latency_ms"]       = int((time.time() - start) * 1000)
        parsed["retrieved_chunks"] = len(retrieved)
        return parsed

    # ── Groq API call ─────────────────────────────────────────────────────
    async def _llm(self, prompt: str) -> str:
        if not GROQ_API_KEY:
            return json.dumps({
                "answer":     "GROQ_API_KEY missing in .env file.",
                "sources":    [], "confidence": "low",
            })
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(
                    GROQ_URL,
                    headers={
                        "Content-Type":  "application/json",
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                    },
                    json={
                        "model":    MODEL,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user",   "content": prompt},
                        ],
                        "max_tokens":  1500,
                        "temperature": 0.05,
                        "top_p":       0.9,
                    },
                )
                if resp.status_code != 200:
                    print(f"Groq {resp.status_code}: {resp.text[:200]}")
                    return json.dumps({
                        "answer":     f"API Error {resp.status_code}. Check .env",
                        "sources":    [], "confidence": "low",
                    })
                return resp.json()["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            return json.dumps({"answer":"Request timed out.","sources":[],"confidence":"low"})
        except Exception as e:
            return json.dumps({"answer":f"Error: {e}","sources":[],"confidence":"low"})

    # ── Smart file section finder ─────────────────────────────────────────
    def _smart_chunk_file(self, content: str, question: str) -> str:
        if len(content) <= 6000:
            return content
        q_words  = [w.strip("?.,!") for w in question.lower().split() if len(w) > 3]
        sections = [s.strip() for s in content.split("\n") if s.strip()]
        scored   = [(sum(1 for w in q_words if w in s.lower()), i, s) for i, s in enumerate(sections)]
        scored.sort(key=lambda x: x[0], reverse=True)
        selected: set = set()
        for _, idx, _ in scored[:10]:
            for j in range(max(0, idx - 2), min(len(sections), idx + 3)):
                selected.add(j)
        result = "\n".join(sections[i] for i in sorted(selected))
        header = content[:800]
        if header not in result:
            result = header + "\n...\n" + result
        return result[:7000]

    # ── Chunk text ────────────────────────────────────────────────────────
    def _chunk(self, text: str, size: int = 512) -> List[str]:
        words = text.split()
        if len(words) <= size:
            return [text]
        chunks: List[str] = []
        cur:    List[str] = []
        cnt = 0
        for w in words:
            cur.append(w); cnt += len(w) + 1
            if cnt >= size:
                chunks.append(" ".join(cur))
                cur = cur[-25:]; cnt = sum(len(w)+1 for w in cur)
        if cur:
            chunks.append(" ".join(cur))
        return chunks

    # ── Keyword frequency embedding ───────────────────────────────────────
    def _embed(self, text: str) -> np.ndarray:
        t     = text.lower()
        total = max(len(t.split()), 1)
        vec   = np.array([float(t.count(k)) / total for k in KEYWORDS], dtype=np.float32)
        norm  = float(np.linalg.norm(vec))
        return vec / norm if norm > 0 else vec

    # ── List documents ────────────────────────────────────────────────────
    def list_docs(self) -> List[Dict]:
        seen:  set       = set()
        docs: List[Dict] = []
        for item in self.store.metadata:
            if item["doc_id"] not in seen:
                seen.add(item["doc_id"])
                docs.append({
                    "doc_id":  item["doc_id"],
                    "title":   item["title"],
                    "preview": item["content"][:100] + "...",
                })
        return docs

    # ── Load from runbooks.txt ────────────────────────────────────────────
    def _load_from_file(self) -> None:
        runbook_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runbooks.txt")
        if not os.path.exists(runbook_path):
            print("⚠️  runbooks.txt not found")
            return
        try:
            import re
            with open(runbook_path, "r", encoding="utf-8") as f:
                full_text = f.read()
            sections = re.split(r"={5,}\s*\nRUNBOOK \d+:", full_text)
            count = 0
            for section in sections[1:]:
                lines      = section.strip().split("\n")
                title_line = lines[0].strip() if lines else ""
                tags_match = re.search(r"Tags:\s*(.+)", section)
                tags       = tags_match.group(1).strip() if tags_match else ""
                content    = "\n".join(lines[1:]).strip()
                if title_line and len(content) > 100:
                    self.ingest(title_line, content, tags)
                    count += 1
            print(f"✅ Loaded {count} runbooks from runbooks.txt")
        except Exception as e:
            print(f"⚠️  runbooks.txt load error: {e}")

    # ── Built-in compact runbooks ─────────────────────────────────────────
    def _load_defaults(self) -> None:
        defaults = [
            ("Kubernetes Quick Reference",
             "kubernetes kubectl quick commands cheatsheet",
             "kubectl get pods/deployments/services/nodes -n <ns>\n"
             "kubectl describe pod/deployment <n>\nkubectl logs <pod> --tail=100 -f\n"
             "kubectl exec -it <pod> -- /bin/bash\nkubectl scale deployment <n> --replicas=3\n"
             "kubectl rollout status/history/undo deployment/<n>\nkubectl top pods/nodes\n"
             "kubectl port-forward <pod> 8080:8080\nkubectl apply -f file.yaml\n"
             "kubectl get events --sort-by='.lastTimestamp'"),

            ("Docker Quick Reference",
             "docker container image commands cheatsheet",
             "docker ps -a\ndocker images\ndocker logs <c> --tail=100 -f\n"
             "docker exec -it <c> /bin/bash\ndocker build -t image:tag .\n"
             "docker push registry/image:tag\ndocker stop <c> && docker rm <c>\n"
             "docker system prune -af --volumes\ndocker stats --no-stream\n"
             "docker inspect <container>"),

            ("Linux Quick Reference",
             "linux commands system admin cheatsheet",
             "systemctl start/stop/restart/status <service>\n"
             "journalctl -u <service> -f -n 100\n"
             "df -h\nfree -h\ntop\nps aux\nnetstat -tuln\n"
             "find / -size +500M -type f\ndu -sh /* | sort -rh | head -20\n"
             "tail -f /var/log/syslog\ngrep -r 'error' /var/log/\n"
             "chmod 755 file\nchown user:group file"),

            ("Git Quick Reference",
             "git version control commands cheatsheet",
             "git clone <url>\ngit status\ngit add .\ngit commit -m 'message'\n"
             "git push origin branch\ngit pull origin main\ngit checkout -b new-branch\n"
             "git merge feature-branch\ngit revert <commit>\ngit log --oneline -20\n"
             "git stash && git stash pop\ngit tag -a v1.0 -m 'version 1.0'\n"
             "git reset --hard HEAD~1"),

            ("PostgreSQL Quick Reference",
             "postgresql postgres database administration queries",
             "psql -h localhost -U postgres -d dbname\n"
             "SELECT * FROM pg_stat_activity WHERE state='active';\n"
             "SELECT pg_size_pretty(pg_database_size('db'));\n"
             "SELECT * FROM pg_locks WHERE NOT granted;\n"
             "VACUUM ANALYZE table_name;\n"
             "pg_dump -U postgres db > backup.sql\n"
             "psql -U postgres db < backup.sql\n"
             "CREATE USER u WITH PASSWORD 'p';\n"
             "GRANT ALL PRIVILEGES ON DATABASE db TO u;"),
        ]
        for title, tags, content in defaults:
            self.ingest(title, content, tags)
