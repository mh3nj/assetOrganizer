"""
archive.py

RAR archive manager.
Uses Rar.exe (console CLI tool) for all operations.
Best compression (-m5), solid (-s), no comments.
"""

from pathlib import Path
import subprocess


class RarArchive:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def _rar_exe(self) -> Path:
        """Use Rar.exe (console) for CLI — more reliable than WinRAR.exe."""
        path = self.config.WINRAR_PATH  # points to Rar.exe
        if path.exists():
            return path
        # fallback to WinRAR.exe if Rar.exe missing
        fallback = self.config.WINRAR_GUI_PATH
        if fallback.exists():
            return fallback
        raise FileNotFoundError(
            "No RAR executable found. Expected at:\n"
            f"  {path}\n  {fallback}"
        )

    def create_rar(self, files, output: Path) -> Path:
        if not files:
            raise ValueError("No files to archive.")
        output = Path(output)
        rar = self._rar_exe()

        command = [
            str(rar),
            "a",
            "-r",
            "-m5",
            "-s",
            "-ep",
            str(output),
        ]
        for file in files:
            command.append(str(file.absolute()))

        self.logger.info(f"Creating RAR: {output.name}")
        self.logger.info(f"  Files: {[f.name for f in files]}")

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            self.logger.error(f"Command: {' '.join(command)}")
            self.logger.error(f"stdout: {result.stdout}")
            self.logger.error(f"stderr: {result.stderr}")
            raise RuntimeError(
                f"RAR failed (exit {result.returncode}) for {output.name}"
            )

        if not output.exists():
            raise RuntimeError(f"RAR file not created: {output.name}")

        size_kb = output.stat().st_size / 1024
        self.logger.info(f"  Created: {output.name} ({size_kb:.1f} KB)")
        return output

    def test_archive(self, archive: Path) -> bool:
        rar = self._rar_exe()
        command = [
            str(rar),
            "t",
            str(archive),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            self.logger.error(f"Test failed: {archive.name}")
            self.logger.error(result.stderr or result.stdout)
            return False
        self.logger.info(f"  Verified OK: {archive.name}")
        return True
