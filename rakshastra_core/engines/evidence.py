import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from rakshastra_core.models import Evidence, Severity, Confidence

class EvidenceStore:
    """Append-only evidence store backed by SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    tool TEXT,
                    host TEXT,
                    timestamp TEXT,
                    finding TEXT,
                    raw_output TEXT,
                    severity TEXT,
                    confidence TEXT,
                    tags TEXT,
                    context TEXT,
                    collector_version TEXT DEFAULT '',
                    command TEXT DEFAULT '',
                    duration REAL DEFAULT 0.0,
                    exit_code INTEGER,
                    checksum TEXT DEFAULT '',
                    platform TEXT DEFAULT ''
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def record(self, evidence: Evidence) -> str:
        """Persist an Evidence object. Returns the evidence ID."""
        tags_str = json.dumps(evidence.tags)
        context_str = json.dumps(evidence.context)
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO evidence 
                (id, created_at, tool, host, timestamp, finding, raw_output,
                 severity, confidence, tags, context,
                 collector_version, command, duration, exit_code, checksum, platform)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.id,
                    evidence.created_at,
                    evidence.tool,
                    evidence.host,
                    evidence.timestamp,
                    evidence.finding,
                    evidence.raw_output,
                    evidence.severity.value if isinstance(evidence.severity, Severity) else str(evidence.severity),
                    evidence.confidence.value if isinstance(evidence.confidence, Confidence) else str(evidence.confidence),
                    tags_str,
                    context_str,
                    evidence.collector_version,
                    evidence.command,
                    evidence.duration,
                    evidence.exit_code,
                    evidence.checksum,
                    evidence.platform
                )
            )
            conn.commit()
        finally:
            conn.close()
        return evidence.id

    def get(self, evidence_id: str) -> Optional[Evidence]:
        """Retrieve a single evidence record."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
            if row:
                return self._row_to_evidence(row)
        finally:
            conn.close()
        return None

    def query(self, *, host: str = None, severity: Severity = None,
              tags: List[str] = None, since: str = None) -> List[Evidence]:
        """Query evidence by filters."""
        query_str = "SELECT * FROM evidence WHERE 1=1"
        params = []

        if host:
            query_str += " AND host = ?"
            params.append(host)
        if severity:
            query_str += " AND severity = ?"
            params.append(severity.value if isinstance(severity, Severity) else str(severity))
        if since:
            query_str += " AND timestamp >= ?"
            params.append(since)

        conn = self._get_connection()
        try:
            rows = conn.execute(query_str, params).fetchall()
            results = [self._row_to_evidence(row) for row in rows]
        finally:
            conn.close()

        if tags:
            filtered = []
            for ev in results:
                if any(tag in ev.tags for tag in tags):
                    filtered.append(ev)
            return filtered

        return results

    def summary(self) -> Dict[str, Any]:
        """Aggregate counts by severity, host, and tag."""
        severity_counts = {}
        host_counts = {}
        tag_counts = {}

        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT severity, host, tags FROM evidence").fetchall()
            for row in rows:
                sev = row["severity"]
                host = row["host"]
                tags = json.loads(row["tags"] or "[]")

                severity_counts[sev] = severity_counts.get(sev, 0) + 1
                host_counts[host] = host_counts.get(host, 0) + 1
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        finally:
            conn.close()

        return {
            "total": len(rows),
            "by_severity": severity_counts,
            "by_host": host_counts,
            "by_tag": tag_counts
        }

    def _row_to_evidence(self, row: sqlite3.Row) -> Evidence:
        tags = []
        try:
            tags = json.loads(row["tags"]) if row["tags"] else []
        except Exception:
            pass

        context = {}
        try:
            context = json.loads(row["context"]) if row["context"] else {}
        except Exception:
            pass

        # Safely read new columns that may not exist in older databases
        def _safe_get(key, default=None):
            try:
                return row[key]
            except (IndexError, KeyError):
                return default

        return Evidence(
            id=row["id"],
            created_at=row["created_at"],
            tool=row["tool"],
            host=row["host"],
            timestamp=row["timestamp"],
            finding=row["finding"],
            raw_output=row["raw_output"],
            severity=Severity(row["severity"]),
            confidence=Confidence(row["confidence"]),
            tags=tags,
            context=context,
            collector_version=_safe_get("collector_version", ""),
            command=_safe_get("command", ""),
            duration=_safe_get("duration", 0.0) or 0.0,
            exit_code=_safe_get("exit_code"),
            checksum=_safe_get("checksum", ""),
            platform=_safe_get("platform", "")
        )
