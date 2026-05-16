"""
OpsRunbook RAG — Advanced Audit & Correctness Engine v2.0
=========================================================
Features:
1. Keyword-match correctness scoring
2. LLM-as-judge using Groq
3. Confidence threshold auto-flagging
4. Advanced analytics and metrics
5. PostgreSQL migration support
"""

from __future__ import annotations

import json
import os
import re
import logging
from typing import Any

import httpx

from database import (
    insert_audit,
    get_audits,
    get_db_metrics,
    update_feedback,
    AppDB,
)

logger = logging.getLogger("audit")

# =========================================================
# DOMAIN KEYWORDS
# =========================================================

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "kubernetes": [
        "kubectl", "pod", "deployment", "namespace",
        "node", "cluster", "ingress", "service",
        "configmap", "secret", "helm", "kube"
    ],

    "docker": [
        "container", "image", "dockerfile",
        "docker", "compose", "registry",
        "volume", "network", "build",
        "push", "pull"
    ],

    "postgresql": [
        "postgres", "psql", "database",
        "query", "table", "index",
        "vacuum", "replication",
        "pg_dump", "schema"
    ],

    "linux": [
        "bash", "linux", "systemctl",
        "journalctl", "cron", "grep",
        "awk", "sed", "chmod",
        "ssh", "kernel", "process"
    ],

    "ci_cd": [
        "pipeline", "jenkins",
        "github actions", "workflow",
        "artifact", "deploy",
        "build", "test", "ci",
        "cd", "release"
    ],

    "nginx": [
        "nginx", "proxy", "upstream",
        "ssl", "tls", "certificate",
        "vhost", "location",
        "reverse proxy", "load balance"
    ],

    "redis": [
        "redis", "cache", "ttl",
        "eviction", "sentinel",
        "cluster", "pub", "sub",
        "rdb", "aof"
    ],

    "terraform": [
        "terraform", "plan", "apply",
        "state", "module", "provider",
        "resource", "variable",
        "output", "backend"
    ],
}

ALL_KEYWORDS: set[str] = {
    kw for kws in DOMAIN_KEYWORDS.values() for kw in kws
}

# =========================================================
# CONFIG
# =========================================================

CONFIDENCE_SUSPECT_THRESHOLD = "low"

CONFIDENCE_SCORE_MAP = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.2
}

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_TIMEOUT = 30

# =========================================================
# DOMAIN DETECTION
# =========================================================

def _detect_domain(text: str) -> str:
    text_lower = text.lower()

    scores = {
        domain: sum(1 for kw in kws if kw in text_lower)
        for domain, kws in DOMAIN_KEYWORDS.items()
    }

    best = max(scores, key=scores.get)

    return best if scores[best] > 0 else "general"

# =========================================================
# KEYWORD MATCH SCORE
# =========================================================

def keyword_match_score(
    question: str,
    answer: str,
    sources_text: str
) -> dict[str, Any]:

    q_lower = question.lower()
    ans_lower = answer.lower()

    relevant = [
        kw for kw in ALL_KEYWORDS
        if kw in q_lower
    ]

    if not relevant:
        return {
            "score": 0.75,
            "matched_kws": [],
            "missing_kws": [],
            "domain": _detect_domain(question),
            "verdict": "pass",
        }

    matched = [
        kw for kw in relevant
        if kw in ans_lower
    ]

    missing = [
        kw for kw in relevant
        if kw not in ans_lower
    ]

    score = len(matched) / len(relevant)

    if score >= 0.75:
        verdict = "pass"

    elif score >= 0.4:
        verdict = "partial"

    else:
        verdict = "fail"

    return {
        "score": round(score, 3),
        "matched_kws": matched,
        "missing_kws": missing,
        "domain": _detect_domain(question),
        "verdict": verdict,
    }

# =========================================================
# CONFIDENCE CHECK
# =========================================================

def confidence_threshold_check(confidence: str) -> dict[str, Any]:

    score = CONFIDENCE_SCORE_MAP.get(confidence, 0.0)

    flagged = (
        confidence == CONFIDENCE_SUSPECT_THRESHOLD
    )

    return {
        "flagged": flagged,
        "reason":
            "Retrieval confidence is low."
            if flagged else "",
        "score": score,
    }

# =========================================================
# GROQ LLM JUDGE
# =========================================================

async def llm_judge_score(
    question: str,
    answer: str,
    sources: str
) -> dict[str, Any]:

    api_key = os.getenv("GROQ_API_KEY", "")

    if not api_key:
        return {
            "score": -1,
            "rationale": "GROQ_API_KEY missing",
            "issues": [],
            "skipped": True,
        }

    system_prompt = (
        "You are an expert DevOps engineer. "
        "Evaluate the AI answer based on "
        "technical accuracy, completeness, "
        "and actionability. "
        "Respond ONLY with valid JSON:\n"
        '{"score": 0, "rationale": "", "issues": []}'
    )

    user_prompt = (
        f"QUESTION:\n{question}\n\n"
        f"SOURCES:\n{sources}\n\n"
        f"ANSWER:\n{answer}"
    )

    try:

        async with httpx.AsyncClient(
            timeout=GROQ_TIMEOUT
        ) as client:

            response = await client.post(
                GROQ_API_URL,

                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },

                json={
                    "model": GROQ_MODEL,
                    "temperature": 0.0,
                    "max_tokens": 256,

                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                }
            )

        data_json = response.json()

        if "choices" not in data_json:
            return {
                "score": -1,
                "rationale": "Invalid API response",
                "issues": [],
                "skipped": True,
            }

        raw = (
            data_json["choices"][0]
            ["message"]["content"]
            .strip()
        )

        raw = re.sub(
            r"^```[a-z]*\n?",
            "",
            raw
        ).rstrip("` \n")

        data = json.loads(raw)

        return {
            "score": int(data.get("score", 5)),
            "rationale": str(
                data.get("rationale", "")
            ),
            "issues": list(
                data.get("issues", [])
            ),
            "skipped": False,
        }

    except Exception as exc:

        logger.warning(
            "llm_judge_score failed: %s",
            exc
        )

        return {
            "score": -1,
            "rationale": str(exc),
            "issues": [],
            "skipped": True,
        }

# =========================================================
# MAIN CORRECTNESS ENGINE
# =========================================================

async def run_correctness_checks(
    question: str,
    answer: str,
    sources: str,
    confidence: str,
) -> dict[str, Any]:

    kw_result = keyword_match_score(
        question,
        answer,
        sources
    )

    conf_result = confidence_threshold_check(
        confidence
    )

    llm_result = await llm_judge_score(
        question,
        answer,
        sources
    )

    kw_score = kw_result["score"]
    conf_score = conf_result["score"]

    if llm_result.get("skipped"):

        overall = (
            0.60 * kw_score
            + 0.40 * conf_score
        )

    else:

        llm_norm = (
            llm_result["score"] / 10.0
        )

        overall = (
            0.30 * kw_score
            + 0.20 * conf_score
            + 0.50 * llm_norm
        )

    if overall >= 0.70:
        verdict = "correct"

    elif overall >= 0.40:
        verdict = "uncertain"

    else:
        verdict = "incorrect"

    auto_flagged = (
        conf_result["flagged"]
        or kw_result["verdict"] == "fail"
        or (
            not llm_result.get("skipped")
            and llm_result["score"] < 4
        )
    )

    return {
        "keyword_match": kw_result,
        "confidence_check": conf_result,
        "llm_judge": llm_result,
        "overall_score": round(overall, 3),
        "overall_verdict": verdict,
        "auto_flagged": auto_flagged,
        "domain": kw_result["domain"],
    }

# =========================================================
# LOG QUERY
# =========================================================

async def log_query(
    user_id: int | None,
    username: str | None,
    token: str | None,
    question: str,
    answer: str,
    sources: list | str,
    latency: int,
    confidence: str,
) -> dict[str, Any]:

    src_str = (
        ", ".join(sources)
        if isinstance(sources, list)
        else str(sources or "")
    )

    log_id = insert_audit(
        user_id,
        username,
        token,
        question,
        answer,
        src_str,
        latency,
        confidence
    )

    try:

        correctness = await run_correctness_checks(
            question,
            answer,
            src_str,
            confidence
        )

    except Exception as exc:

        logger.error(
            "Correctness check error: %s",
            exc
        )

        correctness = {
            "overall_verdict": "unknown",
            "auto_flagged": False,
            "overall_score": -1,
            "domain": "general"
        }

    _save_correctness(
        log_id,
        correctness
    )

    return {
        "log_id": log_id,
        "correctness": correctness
    }

# =========================================================
# SAVE CORRECTNESS
# =========================================================

def _save_correctness(
    log_id: int | None,
    report: dict
) -> None:

    if log_id is None:
        return

    try:

        with AppDB() as (cur, _):

            cur.execute(
                """
                UPDATE audit_logs
                SET correctness_score   = %s,
                    correctness_verdict = %s,
                    domain              = %s,
                    auto_flagged        = %s,
                    llm_judge_score     = %s,
                    llm_judge_rationale = %s,
                    kw_match_score      = %s
                WHERE id = %s
                """,

                (
                    report.get("overall_score"),

                    report.get(
                        "overall_verdict",
                        "unknown"
                    ),

                    report.get(
                        "domain",
                        "general"
                    ),

                    report.get(
                        "auto_flagged",
                        False
                    ),

                    report.get(
                        "llm_judge",
                        {}
                    ).get("score"),

                    report.get(
                        "llm_judge",
                        {}
                    ).get("rationale", ""),

                    report.get(
                        "keyword_match",
                        {}
                    ).get("score"),

                    log_id,
                ),
            )

    except Exception as exc:

        logger.warning(
            "Could not save correctness: %s",
            exc
        )

# =========================================================
# FEEDBACK
# =========================================================

def submit_feedback(
    log_id: int,
    feedback: str
) -> None:

    update_feedback(
        log_id,
        feedback
    )

# =========================================================
# GET LOGS
# =========================================================

def get_logs(limit: int = 500):

    return get_audits(limit)

# =========================================================
# METRICS
# =========================================================

def get_metrics():

    base = get_db_metrics()

    return {
        **base,
        **_get_extended_metrics()
    }

# =========================================================
# EXTENDED METRICS
# =========================================================

def _get_extended_metrics():

    with AppDB() as (cur, _):

        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE latency_ms < 500
                ) AS lt_500,

                COUNT(*) FILTER (
                    WHERE latency_ms
                    BETWEEN 500 AND 999
                ) AS ms_500_1000,

                COUNT(*) FILTER (
                    WHERE latency_ms
                    BETWEEN 1000 AND 1999
                ) AS ms_1000_2000,

                COUNT(*) FILTER (
                    WHERE latency_ms >= 2000
                ) AS gt_2000

            FROM audit_logs
            """
        )

        row = cur.fetchone()

        latency_histogram = [

            {
                "bucket": "<500ms",
                "count": row["lt_500"]
            },

            {
                "bucket": "500-1000ms",
                "count": row["ms_500_1000"]
            },

            {
                "bucket": "1000-2000ms",
                "count": row["ms_1000_2000"]
            },

            {
                "bucket": ">2000ms",
                "count": row["gt_2000"]
            },
        ]

        return {
            "latency_histogram":
                latency_histogram
        }

# =========================================================
# DATABASE MIGRATION
# =========================================================

MIGRATION_SQL = """
ALTER TABLE audit_logs
ADD COLUMN IF NOT EXISTS correctness_score FLOAT,

ADD COLUMN IF NOT EXISTS correctness_verdict
VARCHAR(20),

ADD COLUMN IF NOT EXISTS domain
VARCHAR(40),

ADD COLUMN IF NOT EXISTS auto_flagged
BOOLEAN DEFAULT FALSE,

ADD COLUMN IF NOT EXISTS llm_judge_score
INTEGER,

ADD COLUMN IF NOT EXISTS llm_judge_rationale
TEXT,

ADD COLUMN IF NOT EXISTS kw_match_score
FLOAT;
"""

# =========================================================
# RUN MIGRATION
# =========================================================

def run_migration() -> None:

    try:

        with AppDB() as (cur, _):

            cur.execute(MIGRATION_SQL)

        logger.info(
            "audit_logs migration applied"
        )

    except Exception as exc:

        logger.error(
            "Migration failed: %s",
            exc
        )