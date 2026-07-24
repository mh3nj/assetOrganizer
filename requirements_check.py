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
    if not config.PHOTOSHOP_PATH.exists():
        missing.append("Photoshop (PSD files will fail until this is fixed)")
    if not config.ILLUSTRATOR_PATH.exists():
        missing.append("Illustrator (AI/EPS files will fail until this is fixed)")
    if missing:
        for item in missing:
            warn(item)
    return True
