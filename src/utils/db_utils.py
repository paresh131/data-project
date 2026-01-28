import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from read_utils import AppConfig
from logger_utils import AppLogger

class AirlineDBConnection:
    def __init__(self):
        self.logger = AppLogger().get_logger(__name__)
        self.config = AppConfig()
        self.db_path = self.config.get_db_path()
        self.connection = None

    def __enter__(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.logger.info(f"Database: Connection opened for {self.db_path}")
            return self.connection
        except sqlite3.Error as e:
            self.logger.critical(f"Database Critical: Connection failed: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()
            self.logger.info("Database: Connection closed safely.")
        if exc_type:
            self.logger.error(f"Database Error during transaction: {exc_val}")
        return False