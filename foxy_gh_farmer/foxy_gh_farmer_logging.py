import logging
from pathlib import Path
from typing import Dict

import colorlog
from chia.util.chia_logging import initialize_logging, default_log_level


def add_stdout_handler(logger: logging.Logger, logging_config: Dict):
    service_name = "foxy_gh_farmer"
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
    stdout_handler.setLevel(logging_config.get("log_level", default_log_level))
    logger.addHandler(stdout_handler)


def initialize_logging_with_stdout(logging_config: Dict, root_path: Path):
    service_name = "foxy_gh_farmer"
    initialize_logging(
        service_name=service_name,
        logging_config={
            "log_filename": logging_config["log_filename"],
            "log_level": logging_config["log_level"],
            "log_maxbytesrotation": logging_config["log_maxbytesrotation"],
            "log_maxfilesrotation": logging_config["log_maxfilesrotation"],
            "log_stdout": False,
            "log_syslog": False,
            "log_syslog_host": "127.0.0.1",
            "log_syslog_port": 514,
        },
        root_path=root_path,
    )

    root_logger = logging.getLogger()
    add_stdout_handler(root_logger, logging_config=logging_config)
