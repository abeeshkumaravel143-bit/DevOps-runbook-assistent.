"""
OpsRunbook RAG — Authentication
"""
import secrets
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from database import AUTH_DB, authenticate_user

def create_session(user_id: int) -> str:
    token   = secrets.token_hex(32)
    expires = datetime.utcnow() + timedelta(hours=8)
    conn = psycopg2.connect(**AUTH_DB)
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (%s, %s, %s)",
        (user_id, token, expires)
    )
    conn.commit(); cur.close(); conn.close()
    return token

def get_current_user(token: str):
    if not token: return None
    conn = psycopg2.connect(**AUTH_DB)
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT u.id, u.username, u.role
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = %s AND s.expires_at > NOW()
    """, (token,))
    user = cur.fetchone()
    cur.close(); conn.close()
    return dict(user) if user else None
