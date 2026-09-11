"""
config.example.py

Sanitized public copy of the app configuration — safe to push to GitHub.
This file contains no machine-specific paths.

Setup on a new machine:
    1. Copy this file to `config.py` (config.py is gitignored).
    2. Nothing else required: Adobe / WinRAR paths are auto-detected
       from C:\\Program Files. Override any path below to force it.
"""

import glob
from pathlib import Path


class Config:

    def __init__(self):

        self.BASE_DIR = Path(__file__).parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.DATA_DIR.mkdir(exist_ok=True)

        self.SESSION_FILE = self.DATA_DIR / "session.json"
        self.LOG_FILE = self.DATA_DIR / "organizer.log"

        self.SUPPORTED_SOURCE_EXTENSIONS = [".psd", ".ai"]

        # ── Adobe & WinRAR paths ─────────────────────
        # Auto-detected from C:\Program Files when the configured path
        # doesn't exist. Set an exact path below to force a specific
        # version instead of the newest one found.
        self.PHOTOSHOP_PATH = self._auto_detect(
            Path(r"C:\Program Files\Adobe\Adobe Photoshop\Photoshop.exe"),
            r"C:\Program Files\Adobe\Adobe Photoshop*\Photoshop.exe",
            r"C:\Program Files (x86)\Adobe\Adobe Photoshop*\Photoshop.exe",
        )
        self.ILLUSTRATOR_PATH = self._auto_detect(
            Path(r"C:\Program Files\Adobe\Adobe Illustrator\Support Files\Contents\Windows\Illustrator.exe"),
            r"C:\Program Files\Adobe\Adobe Illustrator*\Support Files\Contents\Windows\Illustrator.exe",
            r"C:\Program Files (x86)\Adobe\Adobe Illustrator*\Support Files\Contents\Windows\Illustrator.exe",
        )
        self.WINRAR_PATH = self._auto_detect(
            Path(r"C:\Program Files\WinRAR\Rar.exe"),
            r"C:\Program Files\WinRAR\Rar.exe",
            r"C:\Program Files (x86)\WinRAR\Rar.exe",
        )
        self.WINRAR_GUI_PATH = self._auto_detect(
            Path(r"C:\Program Files\WinRAR\WinRAR.exe"),
            r"C:\Program Files\WinRAR\WinRAR.exe",
            r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
        )

        self.PREVIEW_WIDTH = 2000
        self.PREVIEW_HEIGHT = 2000
        self.AVIF_QUALITY = 90
        self.AVIF_SPEED = 6
        self.THUMB_WIDTH = 400
        self.THUMB_HEIGHT = 400
        self.THUMB_QUALITY = 70

        # Only the drive holding the source folder is ever written to
        # (PNG/AVIF previews + final RAR live next to the source).
        # A single job needs at most ~1 GB, so requiring 10 GB was excessive.
        self.MINIMUM_FREE_SPACE_GB = 1

        self.ADOBE_STARTUP_WAIT = 20
        self.ADOBE_RECOVERY_WAIT = 20
        self.DOCUMENT_TIMEOUT = 60
        self.MAX_RETRIES = 2

        self.ARCHIVE_PROFILE = {
            "method": "best",
            "solid": True,
            "recovery": False,
            "test": True
        }

        # Locate the JSX scripts folder across all deployment layouts:
        # dev source tree, PyInstaller _internal (with datas), or a plain
        # copy next to the exe. Picks the first one that actually exists.
        self.SCRIPTS_DIR = self._find_scripts_dir()

    @staticmethod
    def _auto_detect(configured: Path, *patterns: str) -> Path:
        if configured.exists():
            return configured
        matches = []
        for pattern in patterns:
            matches.extend(glob.glob(pattern))
        if matches:
            matches.sort()
            return Path(matches[-1])
        return configured

    def _find_scripts_dir(self):
        import sys
        candidates = [self.BASE_DIR / "scripts"]
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).parent
            candidates.append(exe_dir / "_internal" / "scripts")
            candidates.append(exe_dir / "scripts")
        for candidate in candidates:
            if candidate.is_dir():
                return candidate
        return candidates[0]
