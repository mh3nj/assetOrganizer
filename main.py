"""
main.py

Application entry point.
"""

from config import Config
from logger import Logger

from scanner import AssetScanner
from queue import JobQueue

from storage import StorageMonitor
from preview import PreviewProcessor
from archive import RarArchive

from photoshop import PhotoshopController
from illustrator import IllustratorController

from processor import AssetProcessor

from session import SessionManager

from ui import ApplicationUI

from requirements_check import check_environment


def main():

    config = Config()

    logger = Logger(config)
    logger.info("Asset Organizer started.")

    check_environment(config, logger)

    storage = StorageMonitor(config, logger)
    preview = PreviewProcessor(config, logger)
    archive = RarArchive(config, logger)

    photoshop = PhotoshopController(config, logger)
    illustrator = IllustratorController(config, logger)

    processor = AssetProcessor(
        config, logger, preview, archive,
        photoshop, illustrator, storage,
    )

    queue = JobQueue(processor, logger)
    processor.should_continue = lambda: queue.running

    scanner = AssetScanner(config, logger)

    session = SessionManager(config, logger)
    processor.session = session
    queue.session = session

    app = ApplicationUI(config, logger, scanner, queue, session=session)

    logger.set_ui_callback(app.log)

    logger.info("Application ready.")
    app.run()


if __name__ == "__main__":
    main()
