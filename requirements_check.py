"""
requirements_check.py

Verify environment before starting. Warns about anything missing rather
than blocking startup entirely — someone batch-processing only PSDs today
shouldn't be locked out because Illustrator's path changed after an update.
WinRAR is the one hard requirement, since every format needs it at the end
of the pipeline regardless of source app.
"""


def check_environment(config, logger=None):
    warn = logger.warning if logger else print
    missing = []
    if not config.WINRAR_PATH.exists():
        raise RuntimeError(f"WinRAR not found at {config.WINRAR_PATH}. Every asset needs it to archive, so this one can't be skipped.")
    engine = getattr(config, "ENGINE", "adobe")
    if engine == "affinity":
        affinity = getattr(config, "AFFINITY_PATH", None)
        if not affinity or not affinity.exists():
            missing.append(f"Affinity (engine is 'affinity' but not found at {affinity})")
        elif not _mcp_reachable(config):
            missing.append(
                "Affinity MCP server is not answering at "
                f"{config.AFFINITY_MCP_URL} — open Affinity and enable "
                "Settings → MCP Server (jobs will fail until then)"
            )
    else:
        if not config.PHOTOSHOP_PATH.exists():
            missing.append("Photoshop (PSD files will fail until this is fixed)")
        if not config.ILLUSTRATOR_PATH.exists():
            missing.append("Illustrator (AI/EPS files will fail until this is fixed)")
    if missing:
        for item in missing:
            warn(item)
    return True


def _mcp_reachable(config) -> bool:
    """Light TCP probe of the Affinity MCP port — no deps, no handshake."""
    import socket
    host = getattr(config, "AFFINITY_MCP_HOST", "127.0.0.1")
    port = int(getattr(config, "AFFINITY_MCP_PORT", 6767))
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False
