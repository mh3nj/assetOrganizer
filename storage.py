"""
storage.py

Disk space protection.
"""

import shutil
import time
from pathlib import Path


class StorageMonitor:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self._logged_drives = set()

    def free_space_gb(self, path) -> float:
        total, used, free = shutil.disk_usage(path)
        return free / (1024 ** 3)

    def require_space(self, path, should_continue=None):
        drive = Path(path).drive or str(path)
        free = self.free_space_gb(path)
        if drive not in self._logged_drives:
            self._logged_drives.add(drive)
            self.logger.info(f"Free space on {drive}: {free:.2f} GB")
        while free < self.config.MINIMUM_FREE_SPACE_GB:
            if should_continue and not should_continue():
                self.logger.warning("Stopped waiting for disk space — queue was stopped.")
                return False
            self.logger.warning(
                f"Low disk space on {drive} ({free:.2f} GB free). "
                f"Waiting for {self.config.MINIMUM_FREE_SPACE_GB:.1f} GB."
            )
            time.sleep(10)
            free = self.free_space_gb(path)
        return True

    def has_space(self, path) -> bool:
        return self.free_space_gb(path) > self.config.MINIMUM_FREE_SPACE_GB
