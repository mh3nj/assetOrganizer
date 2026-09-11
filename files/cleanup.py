"""
cleanup.py

Safe asset cleanup.
Deletes source PSD/AI only after archive is verified.
Keeps external AVIF for DAM.
"""

from pathlib import Path
import time


class CleanupManager:

    def __init__(self, logger):
        self.logger = logger

    def delete_temp(self, file: Path):
        file = Path(file)
        if not file.exists():
            return
        try:
            file.unlink()
            self.logger.info(f"Deleted temporary file: {file.name}")
        except Exception as error:
            self.logger.warning(f"Could not delete {file.name}: {error}")

    def remove_source(self, job):
        if not job.archive_file:
            raise RuntimeError("Cannot cleanup without archive.")
        archive = Path(job.archive_file)
        if not archive.exists():
            raise RuntimeError(f"Archive does not exist: {archive.name}")

        source = job.source_file
        if not source.exists():
            self.logger.warning(f"Source already gone: {source.name}")
            return

        # Retry loop — Windows sometimes holds file locks briefly
        for attempt in range(5):
            try:
                source.unlink()
                self.logger.info(f"Deleted source: {source.name}")
                return
            except PermissionError:
                if attempt < 4:
                    time.sleep(1)
                else:
                    raise RuntimeError(
                        f"Cannot delete {source.name} — file may be locked. "
                        f"Delete manually once queue finishes."
                    )
            except Exception as error:
                raise RuntimeError(f"Failed to delete {source.name}: {error}")

    def remove_preview(self, job):
        self.logger.info(f"Keeping external preview: {job.preview_file.name}")

    def remove_unknown_files(self, folder: Path):
        check_folder = folder / "CHECK"
        check_folder.mkdir(exist_ok=True)
        supported = [".psd", ".ai", ".avif", ".png", ".jpg", ".jpeg", ".rar"]
        moved = []
        for item in folder.iterdir():
            if item.name == "CHECK":
                continue
            if item.is_file() and item.suffix.lower() not in supported:
                dest = check_folder / item.name
                counter = 1
                while dest.exists():
                    dest = check_folder / f"{item.stem}_{counter}{item.suffix}"
                    counter += 1
                item.rename(dest)
                moved.append(dest)
                self.logger.info(f"Moved unknown: {item.name}")
        return moved
