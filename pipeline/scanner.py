"""
scanner.py

Asset discovery system.
"""

from pathlib import Path
import shutil

from pipeline.job import Job


class AssetScanner:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def scan_folder(self, folder: Path) -> list:
        folder = Path(folder)
        self.logger.info(f"Scanning: {folder}")
        jobs = []
        for item in folder.rglob("*"):
            if not item.is_file():
                continue
            extension = item.suffix.lower()
            if extension in (".psd", ".ai", ".eps"):
                job = Job(item)
                existing = self.find_existing_preview(item)
                if existing:
                    job.existing_preview = existing
                jobs.append(job)
        self.logger.info(f"Found {len(jobs)} Adobe files.")
        return jobs

    def find_existing_preview(self, source: Path):
        extensions = [".png", ".jpg", ".jpeg", ".webp"]
        for ext in extensions:
            candidate = source.with_suffix(ext)
            if candidate.exists():
                return candidate
        return None

    def find_unknown_assets(self, folder: Path):
        check_folder = folder / "CHECK"
        check_folder.mkdir(exist_ok=True)
        supported = [".psd", ".ai", ".avif", ".png", ".jpg", ".jpeg"]
        moved = []
        for item in folder.iterdir():
            if item.name == "CHECK":
                continue
            if item.is_dir():
                files = list(item.rglob("*"))
                has_supported = any(
                    f.suffix.lower() in supported
                    for f in files if f.is_file()
                )
                if not has_supported:
                    destination = check_folder / item.name
                    shutil.move(str(item), str(destination))
                    moved.append(destination)
        self.logger.info(f"Moved {len(moved)} unknown folders.")
        return moved
