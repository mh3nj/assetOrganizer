"""
affinity.py

Unified Affinity (Canva-era) controller.

Same job contract as the Adobe controllers (open / export preview /
hide layers / save / close) but driven through Affinity's local MCP
scripting server instead of COM:

- Files are opened by launching Affinity.exe with the file path.
- Previews come from the MCP render tool (actual canvas pixels —
  no filesystem sandbox involved).
- Hide/save/close run as SDK scripts from scripts/affinity_pipeline.js.
  Those steps are best-effort by design: Affinity builds differ, so a
  failed step logs a warning and the pipeline continues with the
  original file bytes instead of failing the whole job.

The user's own Affinity instance is never quit — close() only quits
an instance this controller launched itself.
"""

import json
import subprocess
import time
from pathlib import Path

from affinity.mcp_client import MCPClient, MCPError


class AffinityController:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.mcp = MCPClient(config.AFFINITY_MCP_URL, logger)
        self._scripts_dir = Path(config.SCRIPTS_DIR)
        self._process = None
        self._launched_here = False
        self._ready = False

    # ── lifecycle ──

    def start(self):
        if self._ready and self.mcp.is_reachable(timeout=2):
            return
        if not self._is_app_running():
            self.logger.info("Launching Affinity...")
            self._process = subprocess.Popen([str(self.config.AFFINITY_PATH)])
            self._launched_here = True
            time.sleep(self.config.AFFINITY_STARTUP_WAIT)
        else:
            self.logger.info("Connected to running Affinity.")
            self._launched_here = False
        self._wait_for_mcp()
        try:
            self.mcp.initialize()
        except MCPError as error:
            raise RuntimeError(
                "Affinity MCP handshake failed. Enable it in Affinity → "
                f"Settings → MCP Server. ({error})"
            )
        self._ready = True
        self._log_probe()
        self.logger.info("Affinity ready.")

    def _is_app_running(self) -> bool:
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Affinity.exe", "/FO", "CSV"],
                capture_output=True, text=True, timeout=15,
            )
            return "Affinity.exe" in result.stdout
        except Exception:
            return False

    def _wait_for_mcp(self):
        deadline = time.time() + self.config.AFFINITY_STARTUP_WAIT
        while time.time() < deadline:
            if self.mcp.is_reachable(timeout=2):
                return
            time.sleep(2)
        raise RuntimeError(
            "Affinity MCP server not reachable at "
            f"{self.config.AFFINITY_MCP_URL}. Enable it in Affinity → "
            "Settings → MCP Server, then retry."
        )

    def is_alive(self) -> bool:
        try:
            return self._is_app_running() and self.mcp.is_reachable(timeout=2)
        except Exception:
            return False

    # ── scripts ──

    def _run_script(self, function: str, argument=None):
        library = self._scripts_dir / "affinity_pipeline.js"
        if not library.exists():
            raise FileNotFoundError(f"Missing Affinity JS: {library}")
        if argument is None:
            call = f"{function}();"
        else:
            safe = str(argument).replace("\\", "/").replace('"', '\\"')
            call = f'{function}("{safe}");'
        return self.mcp.execute_script(library.read_text(encoding="utf-8") + "\n" + call)

    @staticmethod
    def _parse_result(output: str) -> dict:
        """The scripts always print one JSON line last — find it."""
        for line in reversed((output or "").splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    parsed = json.loads(line)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    continue
        return {}

    def _log_probe(self):
        try:
            info = self._parse_result(self._run_script("aoProbe"))
            if info.get("ok"):
                self.logger.info(f"Affinity automation surface: {info}")
        except Exception:
            pass

    # ── pipeline steps ──

    def open_file(self, file: Path):
        self.start()
        self.close_all_documents()
        self.logger.info(f"Opening in Affinity: {file.name}")
        subprocess.Popen([str(self.config.AFFINITY_PATH), str(file)])
        self.wait_until_ready(file.name)

    def wait_until_ready(self, expected_name=None, timeout=None):
        timeout = timeout or self.config.DOCUMENT_TIMEOUT
        wanted = {expected_name.lower()} if expected_name else set()
        if expected_name:
            wanted.add(Path(expected_name).stem.lower())
        start = time.time()
        while True:
            try:
                info = self._parse_result(self._run_script("aoCurrentDocName"))
                current = (info.get("name") or "").lower()
                if current and (not wanted or current in wanted
                                or Path(current).stem in wanted):
                    return True
            except Exception:
                pass
            if time.time() - start > timeout:
                raise TimeoutError(
                    f"Affinity document timeout waiting for {expected_name}."
                )
            time.sleep(2)

    def export_preview(self, output: Path):
        # render_spread needs the open document's session UUID, which
        # only the SDK can tell us — fetch it first, then render.
        # Affinity caps renders at 1024px; the AVIF stage scales anyway.
        info = self._parse_result(self._run_script("aoSessionUuid"))
        session_uuid = info.get("sessionUuid")
        if not session_uuid:
            raise RuntimeError(
                f"Affinity preview failed: no session UUID "
                f"({info.get('error') or 'no open document'})."
            )
        mime, pixels = self.mcp.render_spread(session_uuid, 0)
        self.logger.info(f"Affinity rendered preview ({mime}, {len(pixels) // 1024} KB)")
        Path(output).write_bytes(pixels)

    def hide_layers(self):
        try:
            result = self._parse_result(self._run_script("aoHideVisibleLayers"))
            if result.get("ok"):
                self.logger.info(
                    "Affinity hid artwork layers "
                    f"(method={result.get('method')})."
                )
            else:
                self.logger.warning(
                    "Affinity hide-layers failed "
                    f"({result.get('error') or result.get('tried')}). "
                    "Archiving with layers as-is."
                )
        except Exception as error:
            self.logger.warning(f"Affinity hide-layers skipped: {error}")

    def save(self):
        try:
            result = self._parse_result(self._run_script("aoSave"))
            if result.get("ok"):
                self.logger.info("Affinity document saved.")
            else:
                self.logger.warning(
                    "Affinity save unsupported on this build "
                    f"({result.get('error') or result.get('tried')}). "
                    "Continuing with the file as-is."
                )
        except Exception as error:
            self.logger.warning(f"Affinity save skipped: {error}")

    def close_document(self):
        # Honest logging: 3.2.1 throws NOT_IMPLEMENTED for every close
        # path, so tabs accumulate. Never fail the job over it — the
        # next open still works, and self-launched restarts clear tabs.
        try:
            result = self._parse_result(self._run_script("aoClose"))
            if result.get("ok") and not result.get("alreadyClosed"):
                self.logger.info("Affinity tab closed.")
            elif result.get("alreadyClosed"):
                self.logger.info("Affinity already had no open document.")
            else:
                self.logger.warning(
                    "Affinity cannot close tabs on this build "
                    f"({result.get('error') or result.get('tried')}). "
                    "Tabs will accumulate — close them by hand for big batches."
                )
        except Exception as error:
            self.logger.warning(f"Affinity close skipped: {error}")

    def close_all_documents(self):
        self.close_document()

    # ── recovery / shutdown ──

    def restart(self):
        self.logger.warning("Restarting Affinity (error recovery).")
        self.close_all_documents()
        if self._launched_here and self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
            self._process = None
        self._ready = False
        time.sleep(10)
        self.start()
        time.sleep(self.config.AFFINITY_RECOVERY_WAIT)

    def close(self):
        try:
            self.close_all_documents()
        except Exception:
            pass
        if self._launched_here and self._process:
            try:
                self._process.terminate()
                self.logger.info("Affinity closed.")
            except Exception as error:
                self.logger.warning(str(error))
        self._process = None
        self._ready = False
