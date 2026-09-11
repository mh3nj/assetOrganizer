"""
jsx_bridge.py

Loads and executes Adobe ExtendScript files.
"""

from pathlib import Path


class JSXBridge:

    def __init__(self, scripts_folder, logger):
        self.scripts_folder = Path(scripts_folder)
        self.logger = logger

    def load_script(self, name: str) -> str:
        file = self.scripts_folder / name
        if not file.exists():
            raise FileNotFoundError(f"Missing JSX: {file}")
        return file.read_text(encoding="utf-8")

    def build_call(self, function: str, argument=None) -> str:
        if argument is None:
            return f"{function}();"
        safe = str(argument).replace("\\", "/").replace('"', '\\"')
        return f'{function}("{safe}");'
