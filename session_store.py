"""
session_store.py - Enterprise Persistent Session Engine for Follow-Up Sequences.
Module: Week 5 Microsoft Agent Framework Project
"""

from datetime import datetime, timezone
from enum import Enum
import sqlite3
import json
from typing import Optional, List
from pydantic import BaseModel
from schemas import FollowUpSequence, InboundLeadContext, CadenceStep


class SessionStatus(str, Enum):
    NEW = "NEW"
    DAY_1_SENT = "DAY_1_SENT"
    DAY_3_SENT = "DAY_3_SENT"
    DAY_7_SENT = "DAY_7_SENT"
    REPLIED = "REPLIED"
    CLOSED = "CLOSED"


class LeadSessionRecord(BaseModel):
    lead_id: str
    company_name: str
    status: SessionStatus
    current_step: Optional[CadenceStep] = None
    last_action_timestamp: str
    sequence_data_json: str


class FollowUpSessionStore:
    """
    Enterprise Persistent Session Engine for Lead Follow-Up Sequences.
    Uses SQLite with transaction safety and indexed lookups.
    """

    def __init__(self, db_path: str = "followup_sessions.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Creates the session table and performance index."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lead_sessions (
                    lead_id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_step TEXT,
                    last_action_timestamp TEXT NOT NULL,
                    sequence_data_json TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON lead_sessions (status)
            """)
            conn.commit()

    def create_session(self, context: InboundLeadContext, sequence: FollowUpSequence) -> LeadSessionRecord:
        """Initializes a new persistent lead session with its generated sequence."""
        now_utc = datetime.now(timezone.utc).isoformat()
        sequence_json = sequence.model_dump_json()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO lead_sessions 
                (lead_id, company_name, status, current_step, last_action_timestamp, sequence_data_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                context.lead_id,
                context.company_name,
                SessionStatus.NEW.value,
                None,
                now_utc,
                sequence_json
            ))
            conn.commit()

        return self.get_session(context.lead_id)

    def advance_step(self, lead_id: str, new_step: CadenceStep) -> LeadSessionRecord:
        """Advances the session to the next cadence step and updates the timestamp."""
        now_utc = datetime.now(timezone.utc).isoformat()
        
        status_map = {
            CadenceStep.DAY_1_RECAP: SessionStatus.DAY_1_SENT,
            CadenceStep.DAY_3_VALUE_ADD: SessionStatus.DAY_3_SENT,
            CadenceStep.DAY_7_BREAKUP: SessionStatus.DAY_7_SENT,
        }

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE lead_sessions
                SET status = ?, current_step = ?, last_action_timestamp = ?
                WHERE lead_id = ?
            """, (status_map[new_step].value, new_step.value, now_utc, lead_id))
            conn.commit()

        return self.get_session(lead_id)

    def record_prospect_reply(self, lead_id: str) -> LeadSessionRecord:
        """Immediately halts automated follow-ups when prospect replies."""
        now_utc = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE lead_sessions
                SET status = ?, last_action_timestamp = ?
                WHERE lead_id = ?
            """, (SessionStatus.REPLIED.value, now_utc, lead_id))
            conn.commit()

        return self.get_session(lead_id)

    def get_session(self, lead_id: str) -> Optional[LeadSessionRecord]:
        """Loads a session record from disk by lead_id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT lead_id, company_name, status, current_step, last_action_timestamp, sequence_data_json
                FROM lead_sessions
                WHERE lead_id = ?
            """, (lead_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return LeadSessionRecord(
                lead_id=row[0],
                company_name=row[1],
                status=SessionStatus(row[2]),
                current_step=CadenceStep(row[3]) if row[3] else None,
                last_action_timestamp=row[4],
                sequence_data_json=row[5]
            )


if __name__ == "__main__":
    import os
    from schemas import LeadPriority, EmailMessage

    test_db = "test_followup_sessions.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    store = FollowUpSessionStore(db_path=test_db)

    # 1. Create sample lead & sequence
    context = InboundLeadContext(
        lead_id="lead_101",
        client_name="Sarah Connor",
        client_email="sarah@skynet-defense.com",
        company_name="Cyberdyne Systems",
        meeting_transcript="Discussed enterprise threat detection and autonomous security agents.",
        deal_size_estimate=120000.0,
        priority=LeadPriority.ENTERPRISE
    )

    sequence = FollowUpSequence(
        lead_id=context.lead_id,
        company_name=context.company_name,
        emails=[
            EmailMessage(step=CadenceStep.DAY_1_RECAP, delay_days=1, subject="Recap: Enterprise Defense", body="Great meeting earlier today...", call_to_action="Confirm scope"),
            EmailMessage(step=CadenceStep.DAY_3_VALUE_ADD, delay_days=3, subject="Case Study: Real-time defense", body="Sharing our telemetry benchmark...", call_to_action="Book demo"),
            EmailMessage(step=CadenceStep.DAY_7_BREAKUP, delay_days=7, subject="Final check-in on security sprint", body="Checking in before closing our sprint window...", call_to_action="Claim slot")
        ]
    )

    # 2. Test session creation
    rec1 = store.create_session(context, sequence)
    print("Test 1 (Creation):", rec1.status, "| Current Step:", rec1.current_step)
    assert rec1.status == SessionStatus.NEW
    assert rec1.current_step is None

    # 3. Test advancing to Day 1
    rec2 = store.advance_step(context.lead_id, CadenceStep.DAY_1_RECAP)
    print("Test 2 (Day 1 Sent):", rec2.status, "| Current Step:", rec2.current_step)
    assert rec2.status == SessionStatus.DAY_1_SENT
    assert rec2.current_step == CadenceStep.DAY_1_RECAP

    # 4. Test prospect reply (Immediate Stop Condition)
    rec3 = store.record_prospect_reply(context.lead_id)
    print("Test 3 (Replied):", rec3.status)
    assert rec3.status == SessionStatus.REPLIED

    try:
        if os.path.exists(test_db):
            os.remove(test_db)
    except Exception:
        pass

    print("\n[OK] session_store.py persistent state machine verified with 100% precision!")
