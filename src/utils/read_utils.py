import os
import yaml
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from logger_utils import AppLogger

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class AppConfig(metaclass=Singleton):
    def __init__(self):
        self.logger = AppLogger().get_logger(__name__)
        self.utils_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(os.path.dirname(self.utils_dir))
        self.config_path = os.path.join(self.project_root, 'config', 'config.yaml')
        self.settings = self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                data = yaml.safe_load(file)
                self.logger.info(f"Singleton: Config loaded from {self.config_path}")
                return data
        except Exception as e:
            self.logger.error(f"Config Load Error: {e}")
            return {}

    def get_db_path(self): #
        return self.settings.get('database', {}).get('path', 'aviation.db')

    def get_table_name(self): #
        return self.settings.get('database', {}).get('table_name', 'airline_data')