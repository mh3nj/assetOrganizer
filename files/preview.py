"""
preview.py

Preview generation and conversion.
"""

from pathlib import Path
from PIL import Image
import pillow_avif


class PreviewProcessor:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def find_existing_preview(self, source: Path):
        folder = source.parent
        name = source.stem
        possible = [".png", ".jpg", ".jpeg", ".webp"]
        for ext in possible:
            file = folder / f"{name}{ext}"
            if file.exists():
                self.logger.info(f"Existing preview found: {file.name}")
                return file
        return None

    def convert_to_avif(self, source: Path, output: Path) -> tuple[Path, Path, int, int]:
        """
        Produces two files from a single decode:
          - the full preview (existing behavior, unchanged)
          - a small thumbnail tier for Evoury's grid, next to it as
            "{name}.thumb.avif"

        Returns (full_preview_path, thumb_path, original_width, original_height).
        """
        self.logger.info(f"Converting {source.name} to AVIF")
        image = Image.open(source)
        original_width, original_height = image.size

        # Thumbnail first, from a copy — .thumbnail() mutates in place and
        # we still need the full-size image for the main preview below.
        thumb_output = output.with_suffix(".thumb.avif")
        thumb_image = image.copy()
        thumb_image.thumbnail((self.config.THUMB_WIDTH, self.config.THUMB_HEIGHT))
        thumb_image.save(thumb_output, "AVIF", quality=self.config.THUMB_QUALITY, speed=self.config.AVIF_SPEED)
        if not thumb_output.exists():
            raise RuntimeError("Thumbnail AVIF was not created.")

        image.thumbnail((self.config.PREVIEW_WIDTH, self.config.PREVIEW_HEIGHT))
        image.save(output, "AVIF", quality=self.config.AVIF_QUALITY, speed=self.config.AVIF_SPEED)
        if not output.exists():
            raise RuntimeError("AVIF was not created.")

        return output, thumb_output, original_width, original_height

    def delete_file_safe(self, file: Path):
        try:
            if file.exists():
                file.unlink()
        except Exception as error:
            self.logger.warning(f"Could not delete {file}: {error}")
