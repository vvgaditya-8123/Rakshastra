import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from rakshastra_core.models.workflow import WorkflowState, WorkflowStep

class SecurityWorkflowEngine:
    """Manages the state transitions and step logging of the 9-phase security pipeline."""

    PHASE_SEQUENCE = [
        WorkflowState.RECON,
        WorkflowState.ENUMERATION,
        WorkflowState.COLLECTION,
        WorkflowState.EVIDENCE,
        WorkflowState.ANALYSIS,
        WorkflowState.PRIORITIZATION,
        WorkflowState.RECOMMENDATION,
        WorkflowState.VERIFICATION,
        WorkflowState.REPORT
    ]

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
                CREATE TABLE IF NOT EXISTS workflow_sessions (
                    session_id TEXT PRIMARY KEY,
                    current_phase TEXT,
                    max_phase_index INTEGER DEFAULT 0,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_steps (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    session_id TEXT,
                    phase TEXT,
                    command TEXT,
                    status TEXT,
                    duration REAL,
                    output_summary TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def get_active_phase(self, session_id: str) -> WorkflowState:
        """Get the current phase of the session, defaulting to Recon."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT current_phase FROM workflow_sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            if row:
                return WorkflowState(row["current_phase"])
        finally:
            conn.close()
        return WorkflowState.RECON

    def get_max_phase_index(self, session_id: str) -> int:
        """Get the highest phase index reached so far in the session."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT max_phase_index FROM workflow_sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            if row:
                return row["max_phase_index"]
        finally:
            conn.close()
        return 0

    def transition_to(self, session_id: str, new_phase: WorkflowState) -> bool:
        """Transition the session to a new phase if the validation constraints are met.
        
        Constraints:
        1. Backward transitions are always allowed.
        2. Forward transitions cannot skip steps (e.g. cannot transition to phase N 
           if phase N-1 has never been reached).
        """
        new_index = self.PHASE_SEQUENCE.index(new_phase)
        max_index = self.get_max_phase_index(session_id)

        # Enforce sequence: you cannot transition to new_index if it is greater than max_index + 1
        if new_index > max_index + 1:
            # Transition blocked (skipped steps)
            return False

        updated_max_index = max(max_index, new_index)
        now_str = datetime.utcnow().isoformat() + "Z"

        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_sessions (session_id, current_phase, max_phase_index, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, new_phase.value, updated_max_index, now_str)
            )
            conn.commit()
        finally:
            conn.close()
        return True

    def log_step(self, step: WorkflowStep) -> str:
        """Log a step executed during a specific phase."""
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO workflow_steps (id, created_at, session_id, phase, command, status, duration, output_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step.id,
                    step.created_at,
                    step.session_id,
                    step.phase.value if isinstance(step.phase, WorkflowState) else str(step.phase),
                    step.command,
                    step.status,
                    step.duration,
                    step.output_summary
                )
            )
            conn.commit()
        finally:
            conn.close()
        return step.id

    def get_history(self, session_id: str) -> List[WorkflowStep]:
        """Retrieve the sequence of logged steps for a session."""
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM workflow_steps WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,)
            ).fetchall()
            steps = []
            for row in rows:
                steps.append(WorkflowStep(
                    id=row["id"],
                    created_at=row["created_at"],
                    session_id=row["session_id"],
                    phase=WorkflowState(row["phase"]),
                    command=row["command"],
                    status=row["status"],
                    duration=row["duration"],
                    output_summary=row["output_summary"]
                ))
            return steps
        finally:
            conn.close()
