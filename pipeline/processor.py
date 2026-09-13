"""
processor.py

Main asset processing pipeline.

Pipeline order per asset:
  1. Open PSD/AI in Adobe once
  2. Export PNG preview
  3. Convert PNG to AVIF
  4. Ask user for asset name
  5. Hide visible layers only
  6. Save modified source (keeps original filename while PS has it open)
  7. Close Adobe document tab (saves changes)
  8. Rename source + preview files on disk (PS has released the file)
  9. Create RAR with PSD/AI + AVIF inside
  10. Verify archive
  11. Delete loose source file (keep external AVIF for DAM)
  12. Done
"""

from pathlib import Path

from pipeline.job import JobStatus
from files.naming import NameRequest
from files.filename import FilenameManager
from files.cleanup import CleanupManager
from adobe.recovery import AdobeRecovery


class AssetProcessor:

    def __init__(self, config, logger, preview, archive, photoshop, illustrator, storage, session=None, affinity=None):
        self.config = config
        self.logger = logger
        self.preview = preview
        self.archive = archive
        self.photoshop = photoshop
        self.illustrator = illustrator
        self.affinity = affinity
        self.storage = storage
        self.session = session

        self.name_request = NameRequest()
        self.filename = FilenameManager(logger)
        self.cleanup_manager = CleanupManager(logger)
        self.recovery = AdobeRecovery(config, logger)
        self.should_continue = lambda: True
        self._total_assets = 0
        self._processed = 0
        self._failed = 0

    def process(self, job):
        doc_opened = False
        try:
            if not self.storage.require_space(job.source_file.parent, should_continue=self.should_continue):
                raise RuntimeError("Queue stopped while waiting for disk space.")

            # 1. Open Adobe document (with original filename)
            job.set_status(JobStatus.OPENING)
            self.open_document(job)
            doc_opened = True

            # 2. Export preview PNG
            job.set_status(JobStatus.EXPORTING_PREVIEW)
            png = self.create_png_preview(job)

            # 3. Convert to AVIF (full preview + small thumbnail tier)
            job.set_status(JobStatus.CONVERTING_AVIF)
            job.preview_file, job.thumb_file, job.width, job.height = self.preview.convert_to_avif(
                png, job.source_file.with_suffix(".avif")
            )
            self.preview.delete_file_safe(png)

            # 4. Ask human for name
            job.set_status(JobStatus.WAITING_FOR_NAME)
            self.request_name(job)

            # 5. Hide visible layers
            job.set_status(JobStatus.HIDING_LAYERS)
            self.hide_layers(job)

            # 6. Save source (original filename — PS still has the file)
            job.set_status(JobStatus.SAVING)
            self.save_document(job)

            # 7. Close Adobe tab (saves changes, no dialog)
            self.close_document(job)
            doc_opened = False

            # 8. NOW rename files on disk (PS has released the file)
            job.set_status(JobStatus.RENAMING)
            self.rename_source(job)
            self.rename_preview(job)
            self.rename_thumb(job)

            # 9. Create RAR
            job.set_status(JobStatus.CREATING_ARCHIVE)
            self.create_archive(job)

            # 11. Cleanup
            job.set_status(JobStatus.CLEANUP)
            self.cleanup(job)

            job.set_status(JobStatus.DONE)
            self._processed += 1

        except Exception as error:
            self._failed += 1
            self.handle_error(job, error)
        finally:
            if doc_opened:
                try:
                    self.close_document(job)
                except Exception:
                    pass

    def set_queue_size(self, size: int):
        self._total_assets = size
        self._processed = 0
        self._failed = 0

    def get_summary(self) -> str:
        return (
            f"Queue complete. "
            f"Total: {self._total_assets}, "
            f"Success: {self._processed}, "
            f"Failed: {self._failed}"
        )

    def _use_affinity(self, ext: str) -> bool:
        """Native Affinity files always use Affinity; PSD/AI/EPS follow ENGINE."""
        if ext in (".afphoto", ".afdesign", ".afpub"):
            return True
        return getattr(self.config, "ENGINE", "adobe") == "affinity"

    def _require_affinity(self):
        if not self.affinity:
            raise RuntimeError(
                "Job needs Affinity but no Affinity controller is wired. "
                "Set ENGINE to 'adobe' or check the Affinity setup."
            )
        return self.affinity

    def open_document(self, job):
        ext = job.source_file.suffix.lower()
        if self._use_affinity(ext):
            self._require_affinity().open_file(job.source_file)
        elif ext == ".psd":
            self.photoshop.open_file(job.source_file)
        elif ext in (".ai", ".eps"):
            self.illustrator.open_file(job.source_file)
        else:
            raise RuntimeError(f"Unsupported asset: {job.source_file.suffix}")

    def create_png_preview(self, job) -> Path:
        # Always render fresh from the app so user edits are captured.
        # (Affinity renders JPEG bytes via MCP — still written to the
        # .png sidecar path; the AVIF converter sniffs format via PIL.)
        png = job.source_file.with_suffix(".png")
        ext = job.source_file.suffix.lower()
        if self._use_affinity(ext):
            self._require_affinity().export_preview(png)
        elif ext == ".psd":
            self.photoshop.export_preview(png)
        elif ext in (".ai", ".eps"):
            self.illustrator.export_preview(png)
        else:
            raise RuntimeError("Unknown format.")
        return png

    def request_name(self, job):
        if job.final_name:
            return
        request = self.name_request.request_name(job.preview_file)
        while True:
            user_name = request.wait()
            if request.regenerate_requested:
                self.logger.info(f"Regenerating preview for {job.source_file.name}")
                self._do_regenerate_preview(job)
                request.regenerate_requested = False
                request.event.clear()
                continue
            if not user_name:
                raise RuntimeError("Empty asset name.")
            break
        job.final_name = self.filename.unique_name(
            job.source_file.parent, user_name
        )

    def _do_regenerate_preview(self, job):
        self.save_document(job)
        old_png = job.source_file.with_suffix(".png")
        self.preview.delete_file_safe(old_png)
        png = self.create_png_preview(job)
        if job.preview_file:
            self.preview.delete_file_safe(job.preview_file)
        if job.thumb_file:
            self.preview.delete_file_safe(job.thumb_file)
        job.preview_file, job.thumb_file, job.width, job.height = self.preview.convert_to_avif(
            png, job.source_file.with_suffix(".avif")
        )
        self.preview.delete_file_safe(png)
        self.name_request.preview = job.preview_file
        self.name_request.preview_version += 1
        self.logger.info(f"Preview regenerated for {job.source_file.name}")

    def rename_source(self, job):
        new_source = job.source_file.parent / f"{job.final_name}{job.source_file.suffix}"
        if new_source != job.source_file:
            job.source_file.rename(new_source)
            job.source_file = new_source

    def rename_preview(self, job):
        new_preview = job.preview_file.parent / f"{job.final_name}.avif"
        if new_preview != job.preview_file:
            job.preview_file.rename(new_preview)
            job.preview_file = new_preview

    def rename_thumb(self, job):
        if not job.thumb_file:
            return
        new_thumb = job.thumb_file.parent / f"{job.final_name}.thumb.avif"
        if new_thumb != job.thumb_file:
            job.thumb_file.rename(new_thumb)
            job.thumb_file = new_thumb

    def hide_layers(self, job):
        ext = job.source_file.suffix.lower()
        if self._use_affinity(ext):
            self._require_affinity().hide_layers()
        elif ext == ".psd":
            self.photoshop.hide_layers()
        elif ext in (".ai", ".eps"):
            self.illustrator.hide_layers()

    def save_document(self, job):
        ext = job.source_file.suffix.lower()
        if self._use_affinity(ext):
            self._require_affinity().save()
        elif ext == ".psd":
            self.photoshop.save()
        elif ext in (".ai", ".eps"):
            self.illustrator.save()

    def close_document(self, job):
        ext = job.source_file.suffix.lower()
        if self._use_affinity(ext):
            self._require_affinity().close_document()
        elif ext == ".psd":
            self.photoshop.close_document()
        elif ext in (".ai", ".eps"):
            self.illustrator.close_document()

    def create_archive(self, job):
        folder = job.source_file.parent
        archive = folder / f"{job.final_name}.rar"
        files = [job.source_file, job.preview_file]
        self.archive.create_rar(files, archive)
        if not self.archive.test_archive(archive):
            raise RuntimeError(f"RAR verification failed for {archive.name}.")
        job.archive_file = archive

    def cleanup(self, job):
        self.cleanup_manager.remove_source(job)
        self.cleanup_manager.remove_preview(job)

    def handle_error(self, job, error):
        self.logger.error(f"{job.source_file.name}: {error}")
        if self.recovery.is_recoverable(error) and job.can_retry(self.config.MAX_RETRIES):
            job.increase_retry()
            job.error_message = str(error)
            self.logger.warning("Recoverable Adobe error detected. Restarting.")
            ext = job.source_file.suffix.lower()
            if self._use_affinity(ext):
                self._require_affinity().restart()
            elif ext == ".psd":
                self.photoshop.restart()
            elif ext in (".ai", ".eps"):
                self.illustrator.restart()
            self.recovery.wait_ready()
            self.process(job)
            return
        job.fail(error)
