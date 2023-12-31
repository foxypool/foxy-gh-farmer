from pathlib import Path
from sys import stderr, exit
from typing import Dict

from yaml import safe_dump, safe_load, MarkedYAMLError


def _get_default_config():
    return {
        'plot_directories': [],
        'plot_refresh_interval_seconds': 3600,
        'harvester_num_threads': 30,
        'farmer_reward_address': '',
        'pool_payout_address': '',
        'log_level': 'INFO',
        'listen_host': '127.0.0.1',
        'enable_harvester': True,
        'recompute_hosts': [],
    }


class FoxyConfigManager:
    _file_path: Path

    def __init__(self, file_path: Path):
        self._file_path = file_path

    def has_config(self):
        return self._file_path.exists()

    def load_config(self):
        if self._file_path.exists() is False:
            with open(self._file_path, "w") as f:
                safe_dump(_get_default_config(), f)
        with open(self._file_path, "r") as opened_config_file:
            try:
                config = safe_load(opened_config_file)
            except MarkedYAMLError as e:
                context: str = "" if e.problem_mark is None else f" (line={e.problem_mark.line + 1}, column={e.problem_mark.column + 1})"
                print(f"Failed to parse {self._file_path}: {e.problem}{context}.", file=stderr)
                print(f"Please make sure your config is properly formatted.", file=stderr)

                exit(1)
        return config

    def save_config(self, config: Dict):
        with open(self._file_path, "w") as f:
            safe_dump(config, f)
