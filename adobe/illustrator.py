"""
illustrator.py

Persistent Illustrator controller.
Keeps Illustrator open. Closes only documents.
"""

from pathlib import Path
import time
import subprocess

import win32com.client
from adobe.jsx_bridge import JSXBridge


class IllustratorController:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.app = None
        self.jsx = JSXBridge(config.SCRIPTS_DIR, logger)

    def start(self):
        if self.app:
            return
        self.logger.info("Starting Illustrator...")
        try:
            self.app = win32com.client.Dispatch("Illustrator.Application")
        except Exception:
            subprocess.Popen([str(self.config.ILLUSTRATOR_PATH)])
            time.sleep(self.config.ADOBE_STARTUP_WAIT)
            self.app = win32com.client.Dispatch("Illustrator.Application")
        self.logger.info("Illustrator ready.")

    def open_file(self, file: Path):
        self.start()
        self.close_all_documents()
        self.logger.info(f"Opening in Illustrator: {file.name}")
        self.app.Open(str(file))
        self.wait_until_ready(file.name)

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
                raise TimeoutError("Illustrator document timeout.")
            time.sleep(1)

    def execute(self, script: str):
        self.app.DoJavaScript(script)

    def _run_script(self, function: str, argument=None):
        script = self.jsx.build_call(function, argument)
        full = self.jsx.load_script("illustrator_export.jsx") + "\n" + script
        self.execute(full)

    def export_preview(self, output: Path):
        self._run_script("exportPreview", output)

    def hide_layers(self):
        self._run_script("hideVisibleLayers")

    def save(self):
        self.app.ActiveDocument.Save()

    def close_document(self):
        try:
            self.app.ActiveDocument.Close(2)
            self.logger.info("AI tab closed.")
        except Exception as error:
            self.logger.warning(str(error))

    def close_all_documents(self):
        try:
            while self.app.Documents.Count > 0:
                doc = self.app.Documents.Item(1)
                doc.Close(2)
        except Exception:
            pass

    def restart(self):
        self.logger.warning("Restarting Illustrator.")
        self.close_all_documents()
        try:
            self.app.Quit()
        except Exception:
            pass
        self.app = None
        time.sleep(10)
        self.start()
        time.sleep(self.config.ADOBE_RECOVERY_WAIT)

    def close(self):
        if not self.app:
            return
        try:
            self.close_all_documents()
            self.app.Quit()
            self.app = None
            self.logger.info("Illustrator closed.")
        except Exception as error:
            self.logger.warning(str(error))
