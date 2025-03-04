import os
from pathlib import Path

# Changes cwd to root so that paths can be specified relative to root level - MUST BE BEFORE ANY EVA IMPORTS
ROOT = Path(__file__).resolve().parent.parent.parent # get root dir using pathlib
os.chdir(ROOT) # change cwd to root

import sys
import logging

from EVA.windows.main.main_window import MainWindow
from EVA.core.app import App

logger = logging.getLogger(__name__)
logging.basicConfig(filename='EVA.log', encoding='utf-8', level=logging.DEBUG, filemode="w",
                    format='%(asctime)s %(levelname)s: %(message)s')

logging.getLogger("matplotlib.font_manager").disabled = True

handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

if __name__ == "__main__":
    logging.info("Starting EVA...")
    logger.debug("Root directory: %s", ROOT)

    app = App(sys.argv)
    #QIcon.setThemeName("TangoMFK")

    logger.debug("Initialising main window.")
    app.main_window = MainWindow()
    logger.info("Launching main window.")
    app.main_window.show()
    sys.exit(app.exec())
