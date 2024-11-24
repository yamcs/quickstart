import logging
import sys
from pathlib import Path
from datetime import datetime

# Logger Configuration
LOG_LEVEL = 'INFO'    # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_RATE = 5.0        # How often to log simulation time (seconds)

class SimLogger:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once (singleton pattern)
        if SimLogger._initialized:
            return
            
        # Create logs directory inside SIM directory
        sim_root = Path(__file__).parent  # SIM directory
        self.log_dir = sim_root / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"sim_{timestamp}.log"
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Log initial information
        root_logger = logging.getLogger("SimLogger")
        root_logger.info(f"Log file created at: {log_file}")
        root_logger.info(f"Logging level set to: {LOG_LEVEL}")
        
        SimLogger._initialized = True
        self.logger = root_logger
        
    @staticmethod
    def get_logger(name):
        """Get a logger instance with the specified name"""
        SimLogger()  # Ensure logger is initialized
        return logging.getLogger(name) 