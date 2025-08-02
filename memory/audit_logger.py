import json
import os
from datetime import datetime

# Ensure the audit log directory exists
AUDIT_DIR = "memory/audit_log"
os.makedirs(AUDIT_DIR, exist_ok=True)


def log_step(project_id: str, role: str, step_type: str, content: str, success: bool = True):
    """
    Append a log entry for the given project_id. Each entry includes timestamp, role, step_type, content, and success.
    The log is stored in memory/audit_log/{project_id}.json as a list of entries.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "role": role,
        "step_type": step_type,
        "content": content,
        "success": success
    }
    file_path = os.path.join(AUDIT_DIR, f"{project_id}.json")
    try:
        # Load existing log file if present
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = []
    except json.JSONDecodeError:
        log_data = []

    # Append new entry and save back to file
    log_data.append(log_entry)
    with open(file_path, 'w') as f:
        json.dump(log_data, f, indent=2)


def get_logs(project_id: str):
    """
    Retrieve all log entries for the given project_id as a list, sorted by timestamp.
    Returns an empty list if no log exists for the project.
    """
    file_path = os.path.join(AUDIT_DIR, f"{project_id}.json")
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r') as f:
            log_data = json.load(f)
    except json.JSONDecodeError:
        return []
    # Sort entries by timestamp
    try:
        log_data.sort(key=lambda entry: entry.get("timestamp", ""))
    except Exception:
        pass  # If timestamp format issues, skip sorting
    return log_data

