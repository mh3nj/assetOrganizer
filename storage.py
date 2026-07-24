"""
storage.py

Disk space protection.
"""

import shutil
import time


class StorageMonitor:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def free_space_gb(self, path) -> float:
        total, used, free = shutil.disk_usage(path)
        return free / (1024 ** 3)

    def require_space(self, path, should_continue=None):
        free = self.free_space_gb(path)
        self.logger.info(f"Free space: {free:.2f} GB")
        while free < self.config.MINIMUM_FREE_SPACE_GB:
            if should_continue and not should_continue():
                self.logger.warning("Stopped waiting for disk space — queue was stopped.")
                return False
            self.logger.warning("Low disk space. Waiting.")
            time.sleep(10)
            free = self.free_space_gb(path)
        return True

    def has_space(self, path) -> bool:
        return self.free_space_gb(path) > self.config.MINIMUM_FREE_SPACE_GB
