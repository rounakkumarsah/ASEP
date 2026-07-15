"""
ASEP — Control Plane Audit
"""

import json
from pathlib import Path

class AuditExplorer:
    """Reads and filters the local audit.log for compliance records."""

    def __init__(self, log_dir: str = "logs") -> None:
        self.audit_file = Path(log_dir) / "audit.log"

    def list_records(self, session_id: str | None = None, limit: int = 100) -> list[dict]:
        if not self.audit_file.exists():
            return []

        records = []
        # Read file backwards or just read all and slice for simplicity in Phase 2.3
        try:
            with open(self.audit_file, "r") as f:
                lines = f.readlines()
            
            for line in reversed(lines):
                if not line.strip():
                    continue
                record = json.loads(line)
                
                # Filter by session_id
                if session_id:
                    decision_session = record.get("decision", {}).get("session_id")
                    if decision_session != session_id:
                        continue
                        
                records.append(record)
                if len(records) >= limit:
                    break
        except Exception:
            pass
            
        return records
