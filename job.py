"""
job.py

Asset processing job model.
"""

from pathlib import Path
from enum import Enum


class JobStatus(Enum):
    WAITING = "waiting"
    OPENING = "opening"
    EXPORTING_PREVIEW = "exporting_preview"
    CONVERTING_AVIF = "converting_avif"
    WAITING_FOR_NAME = "waiting_for_name"
    RENAMING = "renaming"
    HIDING_LAYERS = "hiding_layers"
    SAVING = "saving"
    CREATING_ARCHIVE = "creating_archive"
    VERIFYING = "verifying"
    CLEANUP = "cleanup"
    DONE = "done"
    FAILED = "failed"


class Job:

    def __init__(self, source_file: Path):
        self.source_file = source_file
        self.preview_file = None
        self.archive_file = None
        self.final_name = None
        self.status = JobStatus.WAITING
        self.error_message = None
        self.retry_count = 0

    def set_status(self, status: JobStatus):
        self.status = status

    def fail(self, error: Exception):
        self.status = JobStatus.FAILED
        self.error_message = str(error)

    def can_retry(self, max_retries: int) -> bool:
        return self.retry_count < max_retries

    def increase_retry(self):
        self.retry_count += 1

    def is_finished(self) -> bool:
        return self.status == JobStatus.DONE

    def is_failed(self) -> bool:
        return self.status == JobStatus.FAILED
