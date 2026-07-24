"""
adobe_recovery.py

Adobe application health and recovery.
"""

import time


class AdobeRecovery:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def wait_ready(self, seconds=None):
        if seconds is None:
            seconds = self.config.ADOBE_RECOVERY_WAIT
        self.logger.info(f"Waiting {seconds} seconds for Adobe.")
        time.sleep(seconds)

    def is_recoverable(self, error) -> bool:
        message = str(error).lower()
        keywords = [
            "scratch", "disk", "memory",
            "not responding", "general photoshop error",
            "cannot complete",
        ]
        return any(word in message for word in keywords)
