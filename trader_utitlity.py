import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

log_formatter = logging.Formatter('[%(asctime)s]%(message)s')


def _get_trader_dir(temp_name: str) -> Tuple[Path, Path]:
    cwd = Path.cwd()
    temp_path = cwd.joinpath(temp_name)

    if temp_path.exists():
        return cwd, temp_path

    home_path = Path.cwd()
    temp_path = home_path.joinpath(temp_name)

    if not temp_path.exists():
        temp_path.mkdir()
    return home_path, temp_path


TRADER_DIR, TEMP_DIR = _get_trader_dir(".temp")
# print(TEMP_DIR)
sys.path.append(str(TRADER_DIR))


def get_folder_path(folder_name: str) -> Path:
    #
    folder_path = TEMP_DIR.joinpath(folder_name)
    if not folder_path.exists():
        folder_path.mkdir()
    return folder_path


def get_file_logger(filename: str) -> logging.Logger:
    logger = logging.getLogger(filename)
    handler = _get_file_logger_handler(filename)
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)
    return logger


file_handlers: Dict[str, logging.FileHandler] = {}


def _get_file_logger_handler(filename: str) -> logging.Handler:
    handler = file_handlers.get(filename, None)
    if handler is None:
        handler = logging.FileHandler(filename)
        file_handlers[filename] = handler
    return handler


def get_file_path(filename: str) -> Path:
    return TEMP_DIR.joinpath(filename)
