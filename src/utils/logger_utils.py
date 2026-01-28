import os
import yaml
import logging
import logging.config

class AppLogger:
    _initialized = False

    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(os.path.dirname(self.current_dir))
        self.log_config_path = os.path.join(self.project_root, 'config', 'logger.yaml')
        self.log_dir = os.path.join(self.project_root, 'logs')

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        if not AppLogger._initialized:
            self._setup_logging()
            AppLogger._initialized = True

    def _setup_logging(self):
        # Fallback basic configuration
        default_level = logging.INFO
        
        if os.path.exists(self.log_config_path):
            with open(self.log_config_path, 'r') as f:
                content = f.read()
                config = yaml.safe_load(content) if content.strip() else None
                
                # CRITICAL FIX: Check if config is not None before iterating
                if config and isinstance(config, dict) and 'handlers' in config:
                    if 'file' in config['handlers']:
                        config['handlers']['file']['filename'] = os.path.join(self.log_dir, 'app.log')
                    logging.config.dictConfig(config)
                    return
        
        # If file is missing or NoneType, use this
        logging.basicConfig(level=default_level, format='%(asctime)s - %(levelname)s - %(message)s')

    def get_logger(self, name):
        return logging.getLogger(name)