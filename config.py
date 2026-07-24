"""
config.py

Global application configuration.
"""

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
        # Update these to match your installed versions.
        # On first run the app will warn if a path doesn't exist;
        # only WinRAR is a hard requirement.
        self.PHOTOSHOP_PATH = Path(
            r"C:\Program Files\Adobe\Adobe Photoshop [VERSION]\Photoshop.exe"
        )
        self.ILLUSTRATOR_PATH = Path(
            r"C:\Program Files\Adobe\Adobe Illustrator [VERSION]\Support Files\Contents\Windows\Illustrator.exe"
        )
        self.WINRAR_PATH = Path(r"C:\Program Files\WinRAR\Rar.exe")
        self.WINRAR_GUI_PATH = Path(r"C:\Program Files\WinRAR\WinRAR.exe")

        self.PREVIEW_WIDTH = 2000
        self.PREVIEW_HEIGHT = 2000
        self.AVIF_QUALITY = 90
        self.AVIF_SPEED = 6
        self.THUMB_WIDTH = 400
        self.THUMB_HEIGHT = 400
        self.THUMB_QUALITY = 70

        self.MINIMUM_FREE_SPACE_GB = 10

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

        self.SCRIPTS_DIR = self.BASE_DIR / "scripts"
