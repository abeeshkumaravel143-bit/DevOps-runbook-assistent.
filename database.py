"""
OpsRunbook RAG — Database Layer
Two separate PostgreSQL databases (configurable via .env):
  AUTH_DB_NAME  → users, sessions
  APP_DB_NAME   → documents, audit_logs, chat_history
"""
import os, hashlib, secrets
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# ── Auth DB (users, sessions) ─────────────────────────────────────────────
AUTH_DB = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "143abeesh@k"),
    "dbname":   os.getenv("AUTH_DB_NAME","opsrunbook_auth"),
}

# ── App DB (docs, audit, chat) ────────────────────────────────────────────
APP_DB = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "143abeesh@k"),
    "dbname":   os.getenv("APP_DB_NAME", "opsrunbook_app"),
}

_auth_pool = None
_app_pool  = None

def get_auth_pool():
    global _auth_pool
    if _auth_pool is None:
        _auth_pool = pool.ThreadedConnectionPool(1, 10, **AUTH_DB)
    return _auth_pool

def get_app_pool():
    global _app_pool
    if _app_pool is None:
        _app_pool = pool.ThreadedConnectionPool(1, 10, **APP_DB)
    return _app_pool

class AuthDB:
    def __enter__(self):
        self.conn = get_auth_pool().getconn()
        self.conn.autocommit = False
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        return self.cur, self.conn
    def __exit__(self, exc_type, *_):
        if exc_type: self.conn.rollback()
        else: self.conn.commit()
        self.cur.close()
        get_auth_pool().putconn(self.conn)

class AppDB:
    def __enter__(self):
        self.conn = get_app_pool().getconn()
        self.conn.autocommit = False
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        return self.cur, self.conn
    def __exit__(self, exc_type, *_):
        if exc_type: self.conn.rollback()
        else: self.conn.commit()
        self.cur.close()
        get_app_pool().putconn(self.conn)


def _create_db_if_missing(dbname, base_cfg):
    cfg = {k: v for k, v in base_cfg.items() if k != "dbname"}
    try:
        conn = psycopg2.connect(**cfg, dbname="postgres")
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{dbname}'")
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {dbname}")
            print(f"✅ Created database: {dbname}")
        cur.close(); conn.close()
    except Exception as e:
        print(f"DB warning ({dbname}): {e}")


def init_db():
    _create_db_if_missing(AUTH_DB["dbname"], AUTH_DB)
    _create_db_if_missing(APP_DB["dbname"],  APP_DB)

    # ── Auth DB ───────────────────────────────────────────────────────────
    conn = psycopg2.connect(**AUTH_DB)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            SERIAL PRIMARY KEY,
            username      VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            salt          VARCHAR(64)  NOT NULL DEFAULT '',
            role          VARCHAR(20)  DEFAULT 'devops' CHECK (role IN ('admin','devops','viewer')),
            is_active     BOOLEAN DEFAULT TRUE,
            last_login    TIMESTAMP,
            created_at    TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token      VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
    cur.close(); conn.close()

    # ── App DB ────────────────────────────────────────────────────────────
    conn = psycopg2.connect(**APP_DB)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id          SERIAL PRIMARY KEY,
            doc_id      VARCHAR(50) UNIQUE NOT NULL,
            title       VARCHAR(255) NOT NULL,
            content     TEXT NOT NULL,
            tags        VARCHAR(500),
            chunk_count INTEGER DEFAULT 1,
            ingested_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER,
            username      VARCHAR(100),
            session_token VARCHAR(255),
            question      TEXT NOT NULL,
            answer        TEXT,
            sources       VARCHAR(1000),
            latency_ms    INTEGER,
            confidence    VARCHAR(20),
            feedback      VARCHAR(20) CHECK (feedback IN ('helpful','not_helpful',NULL)),
            timestamp     TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER,
            session_token VARCHAR(255) NOT NULL,
            role          VARCHAR(20) CHECK (role IN ('user','assistant')),
            content       TEXT NOT NULL,
            created_at    TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_ts   ON audit_logs(timestamp DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_conf ON audit_logs(confidence)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_sess  ON chat_history(session_token)")
    cur.close(); conn.close()

    print(f"✅ Databases ready: {AUTH_DB['dbname']} + {APP_DB['dbname']}")
    print("👤 No default users — register at /register (first user becomes admin)")


# ── Password Hashing ──────────────────────────────────────────────────────
def _hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(32)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return dk.hex(), salt


# ── User Management (Auth DB) ─────────────────────────────────────────────
def register_user(username: str, password: str, role: str = "devops"):
    if len(username) < 3: raise ValueError("Username must be ≥3 characters")
    if len(password) < 6: raise ValueError("Password must be ≥6 characters")
    if role not in ("admin","devops","viewer"): raise ValueError("Invalid role")
    ph, salt = _hash_password(password)
    with AuthDB() as (cur, _):
        try:
            cur.execute(
                "INSERT INTO users (username,password_hash,salt,role) VALUES (%s,%s,%s,%s) RETURNING id,username,role,created_at",
                (username, ph, salt, role)
            )
            return dict(cur.fetchone())
        except psycopg2.errors.UniqueViolation:
            raise ValueError(f"Username '{username}' already exists")

def authenticate_user(username: str, password: str):
    with AuthDB() as (cur, _):
        cur.execute("SELECT id,username,role,password_hash,salt,is_active FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
    if not row or not row["is_active"]: return None
    salt = row["salt"]
    if salt:
        ph, _ = _hash_password(password, salt)
        ok = (ph == row["password_hash"])
    else:
        ok = (hashlib.sha256(password.encode()).hexdigest() == row["password_hash"])
    if ok:
        with AuthDB() as (cur, _):
            cur.execute("UPDATE users SET last_login=NOW() WHERE id=%s", (row["id"],))
        return {"id": row["id"], "username": row["username"], "role": row["role"]}
    return None

def get_all_users():
    with AuthDB() as (cur, _):
        cur.execute("SELECT id,username,role,is_active,last_login,created_at FROM users ORDER BY created_at DESC")
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            for k in ("last_login","created_at"):
                if d.get(k): d[k] = str(d[k])
            rows.append(d)
        return rows

def count_users():
    with AuthDB() as (cur, _):
        cur.execute("SELECT COUNT(*) AS c FROM users")
        return cur.fetchone()["c"]

def set_user_active(user_id: int, is_active: bool):
    with AuthDB() as (cur, _):
        cur.execute("UPDATE users SET is_active=%s WHERE id=%s", (is_active, user_id))

def update_user_role(user_id: int, role: str):
    with AuthDB() as (cur, _):
        cur.execute("UPDATE users SET role=%s WHERE id=%s", (role, user_id))

def delete_user(user_id: int):
    with AuthDB() as (cur, _):
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))


# ── Documents (App DB) ────────────────────────────────────────────────────
def insert_document(doc_id, title, content, tags, chunk_count):
    with AppDB() as (cur, _):
        cur.execute("""
            INSERT INTO documents (doc_id,title,content,tags,chunk_count)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (doc_id) DO UPDATE
            SET content=EXCLUDED.content, tags=EXCLUDED.tags, chunk_count=EXCLUDED.chunk_count
        """, (doc_id, title, content, tags, chunk_count))

def get_all_documents():
    with AppDB() as (cur, _):
        cur.execute("SELECT * FROM documents ORDER BY ingested_at DESC")
        return cur.fetchall()


# ── Audit Logs (App DB) ───────────────────────────────────────────────────
def insert_audit(user_id, username, token, question, answer, sources, latency, confidence):
    with AppDB() as (cur, _):
        cur.execute("""
            INSERT INTO audit_logs (user_id,username,session_token,question,answer,sources,latency_ms,confidence)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (user_id, username, token, question, answer, sources, latency, confidence))
        row = cur.fetchone()
        return row["id"] if row else None

def update_feedback(log_id, feedback):
    with AppDB() as (cur, _):
        cur.execute("UPDATE audit_logs SET feedback=%s WHERE id=%s", (feedback, log_id))

def get_audits(limit=500):
    with AppDB() as (cur, _):
        cur.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT %s", (limit,))
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("timestamp"): d["timestamp"] = str(d["timestamp"])
            rows.append(d)
        return rows

def get_db_metrics():
    with AppDB() as (cur, _):
        cur.execute("SELECT COUNT(*) AS total FROM audit_logs")
        total = cur.fetchone()["total"]

        cur.execute("SELECT AVG(latency_ms) AS avg FROM audit_logs")
        avg = cur.fetchone()["avg"] or 0

        cur.execute("SELECT COUNT(*) AS h FROM audit_logs WHERE feedback='helpful'")
        helpful = cur.fetchone()["h"]

        cur.execute("SELECT COUNT(*) AS nh FROM audit_logs WHERE feedback='not_helpful'")
        not_helpful = cur.fetchone()["nh"]

        # Daily query volume (14 days)
        cur.execute("""
            SELECT DATE(timestamp) AS d, COUNT(*) AS c
            FROM audit_logs GROUP BY DATE(timestamp) ORDER BY d DESC LIMIT 14
        """)
        daily = [{"d": str(r["d"]), "c": r["c"]} for r in cur.fetchall()]

        # Confidence breakdown
        cur.execute("SELECT confidence, COUNT(*) AS c FROM audit_logs GROUP BY confidence")
        conf = [dict(r) for r in cur.fetchall()]

        # Accuracy trend per day
        cur.execute("""
            SELECT DATE(timestamp) AS d,
                COUNT(*) FILTER (WHERE feedback='helpful') AS helpful_c,
                COUNT(*) FILTER (WHERE feedback IS NOT NULL) AS total_fb,
                ROUND(100.0*COUNT(*) FILTER (WHERE feedback='helpful')/
                    NULLIF(COUNT(*) FILTER (WHERE feedback IS NOT NULL),0),1) AS accuracy_pct
            FROM audit_logs GROUP BY DATE(timestamp) ORDER BY d DESC LIMIT 14
        """)
        accuracy_trend = [{"d": str(r["d"]), "pct": float(r["accuracy_pct"] or 0),
                           "helpful": r["helpful_c"], "total_fb": r["total_fb"]} for r in cur.fetchall()]

        # Latency trend per day
        cur.execute("""
            SELECT DATE(timestamp) AS d, ROUND(AVG(latency_ms)) AS avg_lat
            FROM audit_logs GROUP BY DATE(timestamp) ORDER BY d DESC LIMIT 14
        """)
        latency_trend = [{"d": str(r["d"]), "lat": float(r["avg_lat"] or 0)} for r in cur.fetchall()]

        # Confidence vs accuracy
        cur.execute("""
            SELECT confidence, COUNT(*) AS total,
                COUNT(*) FILTER (WHERE feedback='helpful') AS helpful_c,
                ROUND(100.0*COUNT(*) FILTER (WHERE feedback='helpful')/
                    NULLIF(COUNT(*) FILTER (WHERE feedback IS NOT NULL),0),1) AS accuracy_pct
            FROM audit_logs GROUP BY confidence
        """)
        conf_accuracy = [dict(r) for r in cur.fetchall()]

        # Top users
        cur.execute("""
            SELECT username, COUNT(*) AS query_count
            FROM audit_logs WHERE username IS NOT NULL
            GROUP BY username ORDER BY query_count DESC LIMIT 5
        """)
        top_users = [dict(r) for r in cur.fetchall()]

        # Leaderboard: best answers ranked by confidence + helpful feedback
        cur.execute("""
            SELECT username, question,
                answer, confidence, latency_ms, timestamp,
                CASE confidence WHEN 'high' THEN 3 WHEN 'medium' THEN 2 ELSE 1 END AS conf_score
            FROM audit_logs
            WHERE feedback='helpful' AND confidence IS NOT NULL
            ORDER BY conf_score DESC, latency_ms ASC
            LIMIT 10
        """)
        leaderboard = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("timestamp"): d["timestamp"] = str(d["timestamp"])
            leaderboard.append(d)

    user_count = count_users()
    return {
        "total":          total,
        "avg_latency":    round(float(avg), 1),
        "helpful":        helpful,
        "not_helpful":    not_helpful,
        "daily":          daily,
        "confidence":     conf,
        "accuracy_trend": accuracy_trend,
        "latency_trend":  latency_trend,
        "conf_accuracy":  conf_accuracy,
        "top_users":      top_users,
        "leaderboard":    leaderboard,
        "user_count":     user_count,
    }


# ── Chat History (App DB) ─────────────────────────────────────────────────
def save_chat(user_id, token, role, content):
    with AppDB() as (cur, _):
        cur.execute(
            "INSERT INTO chat_history (user_id,session_token,role,content) VALUES (%s,%s,%s,%s)",
            (user_id, token, role, content)
        )

def get_chat_history(token, limit=50):
    with AppDB() as (cur, _):
        cur.execute("""
            SELECT role, content, created_at FROM chat_history
            WHERE session_token=%s ORDER BY created_at DESC LIMIT %s
        """, (token, limit))
        rows = cur.fetchall()
        return [{"role": r["role"], "content": r["content"], "created_at": str(r["created_at"])} for r in reversed(rows)]
