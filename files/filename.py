"""
filename.py

Asset naming manager.
"""

from pathlib import Path


class FilenameManager:

    def __init__(self, logger):
        self.logger = logger

    def normalize(self, name: str) -> str:
        name = name.strip()
        invalid = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid:
            name = name.replace(char, "")
        return name

    def exists(self, folder: Path, name: str) -> bool:
        folder = Path(folder)
        extensions = [".psd", ".ai", ".avif", ".rar"]
        for ext in extensions:
            if (folder / f"{name}{ext}").exists():
                return True
        return False

    def unique_name(self, folder: Path, name: str) -> str:
        name = self.normalize(name)
        if not self.exists(folder, name):
            return name
        counter = 2
        while True:
            new_name = f"{name}{counter}"
            if not self.exists(folder, new_name):
                return new_name
            counter += 1
