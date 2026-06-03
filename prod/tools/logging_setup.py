#!/usr/bin/env python3
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

def configure_logging(script_name: str | None = None, level=logging.INFO):
    repo_root = Path(__file__).resolve().parent.parent.parent
    logs_dir = repo_root / "prod" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "ralph_tools.log"

    logger = logging.getLogger()
    if logger.handlers:
        return

    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = RotatingFileHandler(str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
    fh.setLevel(level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    name = script_name or Path(sys.argv[0]).name
    logger.info(f"Starting {name} (logging initialized).")
