import json
import logging
import time
import matplotlib.pyplot
from PyQt6.QtCore import QThreadPool, pyqtSignal

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from EVA.core.settings.config import Config
from EVA.core.data_loading import load_mu_xray_db, load_gamma_db
from EVA.util.path_handler import get_path
from EVA.util.worker import Worker

logger = logging.getLogger(__name__)


def get_app():
    """
    Shorthand function to quickly access the App instance.

    Returns:
        Instance of App currently running.
    """
    return QApplication.instance()


def get_config():
    """
    Shorthand function to get the Config object instance from App.

    Returns:
        Instance of Config from the App.
    """
    return get_app().config


class App(QApplication):
    """
    The app class contains all settings, parameters, etc. of the app. It has a single instance (created in main.py)
    which can be accessed anywhere using QApplication.instance(). The instance can easily be returned using the
    shorthand function get_app().
    """

    # Emitted (on the main thread) once all databases are loaded and self.muon_database is set.
    databases_loaded = pyqtSignal()
    database_load_error = pyqtSignal(tuple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = None
        self.setWindowIcon(QIcon(get_path("icon.ico")))

        # store config in app
        self.config = Config()

        # thread pool needs to exist before we can hand it work
        self.threadpool = QThreadPool()
        logger.debug(
            "Created thread pool. Maximum thread count: %s",
            self.threadpool.maxThreadCount(),
        )

        # placeholders - populated once the background load finishes
        self.gamma_database = None
        self.mudirac_muon_database_with_intensity = None
        self.mudirac_muon_database = None
        self.legacy_muon_database = None
        self.e_xray_database = None
        self.muon_database = None
        self._databases_ready = False

        self.load_databases()

    def load_databases(self):
        worker = Worker(self._load_databases)
        worker.signals.result.connect(self._on_databases_loaded)
        worker.signals.error.connect(self._on_database_load_error)
        # keep a reference until it's done, just to be safe
        self._db_worker = worker
        self.threadpool.start(worker)

    @staticmethod
    def _load_databases(progress_callback=None):
        """Load databases on a separate thread using a Worker client to reduce load time."""
        t0 = time.time_ns()

        databases = {
            "gamma_database": load_gamma_db.load_gamma_data(),
            "mudirac_muon_database_with_intensity": load_mu_xray_db.load_mudirac_data(),
            "mudirac_muon_database": load_mu_xray_db.load_extended_mudirac_data(),
            "legacy_muon_database": load_mu_xray_db.load_legacy_data(),
        }

        with open(
            get_path("src/EVA/databases/electronic_xrays/xray_booklet_data.json")
        ) as e_xray_file:
            databases["e_xray_database"] = json.load(e_xray_file)

        logger.debug("Loaded all databases in %ss.", (time.time_ns() - t0) / 1e9)
        return databases

    def _on_databases_loaded(self, databases):
        """Called once database dicts have been generated. Fetches individual db and assigns it to memory"""
        self.gamma_database = databases["gamma_database"]
        self.mudirac_muon_database_with_intensity = databases["mudirac_muon_database_with_intensity"]
        self.mudirac_muon_database = databases["mudirac_muon_database"]
        self.legacy_muon_database = databases["legacy_muon_database"]
        self.e_xray_database = databases["e_xray_database"]

        if self.config["database"]["mu_xray_db"] == "legacy":
            self.muon_database = self.legacy_muon_database
            logger.info("Using legacy muon database.")
        elif self.config["database"]["mu_xray_db"] == "mudirac":
            self.muon_database = self.mudirac_muon_database
            logger.info("Using mudirac muon database.")
        else:
            raise KeyError("Invalid muon database in config")

        self._databases_ready = True
        self._db_worker = None
        self.databases_loaded.emit()

    def _on_database_load_error(self, error_info):
        exctype, value, tb = error_info
        logger.error("Failed to load databases: %s", value)
        logger.error(tb)
        self._db_worker = None
        self.database_load_error.emit(error_info)

    def use_mudirac_muon_db(self):
        """
        Sets current muonic X-ray database in App to mudirac and updates configurations.
        """
        self.muon_database = self.mudirac_muon_database
        self.config["database"]["mu_xray_db"] = "mudirac"
        logger.info("Muon database has been set to mudirac.")

    def use_legacy_muon_db(self):
        """
        Sets current muonic X-ray database in App to legacy and updates configurations.
        """
        self.muon_database = self.legacy_muon_database
        self.config["database"]["mu_xray_db"] = "legacy"
        logger.info("Muon database has been set to legacy.")

    # reset the app to its initial state
    def reset(self):
        """
        Resets app to its initial state by restoring to default configs, deleting the main window, resetting database
        to what is specified in config and closing all matplotlib figures.

        Raises:
            KeyError: If current muon database in config is invalid.
        """
        self.config.restore_defaults()
        self.main_window = (
            None  # "delete" main window - garbage collection will take care of it
        )

        # Check config and set default "muon database" accordingly
        if self.config["database"]["mu_xray_db"] == "legacy":
            self.muon_database = self.legacy_muon_database
        elif self.config["database"]["mu_xray_db"] == "mudirac":
            self.muon_database = self.mudirac_muon_database
        else:
            raise KeyError("Invalid muon database in config")

        matplotlib.pyplot.close()
