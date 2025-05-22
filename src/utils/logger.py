import logging.config
import yaml
import os
from pathlib import Path


def setup_logging(config_path="config/logging.yaml"):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Ensure log directory exists
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)

    # Set log path in environment
    os.environ["LOG_PATH"] = str(log_path)

    logging.config.dictConfig(config)
    return logging.getLogger(__name__)
