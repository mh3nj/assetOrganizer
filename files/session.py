"""
session.py

Persistent queue/session storage.
"""

import json
from pathlib import Path


class SessionManager:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def save(self, jobs):
        data = []
        for job in jobs:
            data.append({
                "source": str(job.source_file),
                "preview": str(job.preview_file) if job.preview_file else None,
                "archive": str(job.archive_file) if job.archive_file else None,
                "name": job.final_name,
                "status": job.status.value,
                "error": job.error_message,
                "retry": job.retry_count,
            })
        with open(self.config.SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        self.logger.info("Session saved.")

    def load(self):
        file = self.config.SESSION_FILE
        if not file.exists():
            return []
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.logger.info("Session loaded.")
        return data

    def failed_jobs(self):
        """
        Entries from the last session that never reached "done". Filters to
        ones whose source file is still on disk — a job only gets renamed
        after it fully succeeds, so an incomplete job's source is always
        still sitting at its original path, safe to reprocess from scratch.
        """
        recoverable = []
        for entry in self.load():
            if entry.get("status") == "done":
                continue
            source = Path(entry["source"])
            if source.exists():
                recoverable.append(source)
            else:
                self.logger.warning(f"Skipping unrecoverable session entry (source missing): {entry['source']}")
        return recoverable
