import logging
from pathlib import Path
from typing import Dict

import colorlog
from chia.util.chia_logging import initialize_logging, default_log_level


def initialize_logging_with_stdout(logging_config: Dict, root_path: Path):
    service_name = "foxy_gh_farmer"
    initialize_logging(
        service_name=service_name,
        logging_config={
            "log_filename": "log/debug.log",
            "log_level": "INFO",
            "log_maxbytessrotation": 52428800,
            "log_maxfilesrotation": 7,
            "log_stdout": False,
            "log_syslog": False,
            "log_syslog_host": "127.0.0.1",
            "log_syslog_port": 514,
        },
        root_path=root_path,
    )
    file_name_length = 33 - len(service_name)
    log_date_format = "%Y-%m-%dT%H:%M:%S"
    stdout_handler = colorlog.StreamHandler()
    stdout_handler.setFormatter(
        colorlog.ColoredFormatter(
            f"%(asctime)s.%(msecs)03d {service_name} %(name)-{file_name_length}s: "
            f"%(log_color)s%(levelname)-8s%(reset)s %(message)s",
            datefmt=log_date_format,
            reset=True,
        )
    )
    log_level = logging_config.get("log_level", default_log_level)
    stdout_handler.setLevel(log_level)
    root_logger = logging.getLogger()
    root_logger.addHandler(stdout_handler)
