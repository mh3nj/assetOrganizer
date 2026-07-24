"""
queue.py

Processing queue manager.
"""

import threading
import time


class JobQueue:

    def __init__(self, processor, logger, session=None):
        self.processor = processor
        self.logger = logger
        self.session = session
        self.jobs = []
        self.thread = None
        self.running = False
        self.paused = False

    def add_jobs(self, jobs):
        self.jobs.extend(jobs)
        self.logger.info(f"Added {len(jobs)} jobs.")

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.processor.set_queue_size(len(self.jobs))
        self.running = True
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.thread.start()

    def worker(self):
        self.logger.info("Queue started.")
        for job in self.jobs:
            if not self.running:
                break
            while self.paused:
                time.sleep(1)
            if job.status.value == "done":
                continue
            try:
                self.logger.info(f"Processing {job.source_file.name}")
                self.processor.process(job)
            except Exception as error:
                self.logger.error(str(error))
            finally:
                if self.session:
                    self.session.save(self.jobs)
        self.running = False
        self.logger.info("=" * 50)
        self.logger.info(self.processor.get_summary())
        self.logger.info("=" * 50)
        # Close Adobe applications when queue is fully done
        try:
            self.processor.photoshop.close()
        except Exception:
            pass
        try:
            self.processor.illustrator.close()
        except Exception:
            pass

    def pause(self):
        self.paused = True
        self.logger.info("Queue paused.")

    def resume(self):
        self.paused = False
        self.logger.info("Queue resumed.")

    def stop(self):
        self.running = False
        self.logger.warning("Queue stopped.")
