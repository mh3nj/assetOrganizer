"""
photoshop.py

Persistent Photoshop controller.
Keeps Photoshop open. Closes only documents.
Restarts only when cache is full or queue ends.
"""

from pathlib import Path
import time
import subprocess

import win32com.client
from win32com.client import Dispatch, GetActiveObject
from pywintypes import com_error
from jsx_bridge import JSXBridge


class PhotoshopController:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.app = None
        self.jsx = JSXBridge(config.SCRIPTS_DIR, logger)
        self._launched_photoshop = False
        self._files_opened = 0

    def start(self):
        if self.app:
            return

        # Try connecting to an already-running instance first.
        # GetActiveObject attaches without modifying its UI state.
        try:
            self.app = GetActiveObject("Photoshop.Application")
            self.logger.info("Connected to running Photoshop.")
            self._launched_photoshop = False
            return
        except com_error:
            pass

        # No running instance found — launch and dispatch.
        self.logger.info("Launching Photoshop...")
        try:
            self.app = Dispatch("Photoshop.Application")
        except Exception:
            subprocess.Popen([str(self.config.PHOTOSHOP_PATH)])
            time.sleep(self.config.ADOBE_STARTUP_WAIT)
            self.app = Dispatch("Photoshop.Application")

        # Only toggle Visible when WE launched it, not when attaching
        self.app.Visible = True
        self._launched_photoshop = True
        self.logger.info("Photoshop ready.")

    def is_alive(self) -> bool:
        try:
            return self.app is not None
        except Exception:
            return False

    def open_file(self, file: Path):
        self.start()
        self.close_all_documents()
        self.logger.info(f"Opening PSD: {file.name}")
        self.app.Open(str(file))
        self.wait_until_ready(file.name)
        self._files_opened += 1

    def wait_until_ready(self, expected_name=None, timeout=60):
        start = time.time()
        while True:
            try:
                if self.app.Documents.Count > 0:
                    if expected_name:
                        doc = self.app.ActiveDocument
                        if doc and doc.Name.lower() == expected_name.lower():
                            return True
                    else:
                        return True
            except Exception:
                pass
            if time.time() - start > timeout:
                raise TimeoutError("Photoshop document timeout.")
            time.sleep(1)

    def execute(self, script: str):
        self.app.DoJavaScript(script)

    def _run_script(self, function: str, argument=None):
        script = self.jsx.build_call(function, argument)
        full = self.jsx.load_script("photoshop_export.jsx") + "\n" + script
        self.execute(full)

    def export_preview(self, output: Path):
        self._run_script("exportPreview", output)

    def hide_layers(self):
        self._run_script("hideVisibleLayers")

    def save(self):
        # Use COM Save directly for reliability (avoids path issues)
        self.app.ActiveDocument.Save()

    def close_document(self):
        try:
            # 2 = psSaveChanges — saves before closing, no dialog
            self.app.ActiveDocument.Close(2)
            self.logger.info("PSD tab closed.")
        except Exception as error:
            self.logger.warning(str(error))

    def close_all_documents(self):
        """Close all open documents without dialogs."""
        try:
            while self.app.Documents.Count > 0:
                doc = self.app.Documents.Item(1)
                doc.Close(2)  # psSaveChanges
        except Exception:
            pass

    def restart(self):
        self.logger.warning("Restarting Photoshop (cache/error recovery).")
        # Close all docs first to avoid save prompts
        self.close_all_documents()
        try:
            self.app.Quit()
        except Exception:
            pass
        self.app = None
        time.sleep(10)
        self.start()
        time.sleep(self.config.ADOBE_RECOVERY_WAIT)

    def needs_restart(self, interval: int = 10) -> bool:
        return self._files_opened > 0 and self._files_opened % interval == 0

    def close(self):
        if not self.app:
            return
        try:
            self.close_all_documents()
            self.app.Quit()
            self.app = None
            self.logger.info("Photoshop closed.")
        except Exception as error:
            self.logger.warning(str(error))
