import logging
import sys
from logging import config as logging_config
from pathlib import Path

import coloredlogs
import yaml

import pkm_trade_spoofer

LOGGER = logging.getLogger(__name__)
if hasattr(sys, "_MEIPASS"):
    _CONFIG_PATH = Path(sys._MEIPASS) / "configs/logging.yaml"
else:
    _CONFIG_PATH = Path(pkm_trade_spoofer.__file__).parent / "configs/logging.yaml"


class PokemonPacketsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().startswith("Pokemon packet: ")


class NoPokemonPacketsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.getMessage().startswith("Pokemon packet: ")


def setup_logging(
    config_path: Path = _CONFIG_PATH,
    default_level: int = logging.INFO,
) -> None:
    if config_path.exists():
        with open(config_path, "rt") as f:
            try:
                config = yaml.safe_load(f.read())
                logging_config.dictConfig(config)
                coloredlogs.install()
            except Exception as e:
                logging.basicConfig(level=default_level)
                coloredlogs.install(level=default_level)
                LOGGER.exception(e)
                LOGGER.error("Error in Logging Configuration. Using default configs")
    else:
        logging.basicConfig(level=default_level)
        coloredlogs.install(level=default_level)
        LOGGER.error("Failed to load configuration file. Using default configs")


def get_logger(logger_name: str) -> logging.Logger:
    """Creates a logger object with `logger_name`.

    Args:
        logger_name (str): Logger name

    Returns:
        logging.Logger: Logger object
    """
    setup_logging()
    return logging.getLogger(logger_name)
