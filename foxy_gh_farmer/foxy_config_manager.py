from pathlib import Path
from typing import Dict

from yaml import safe_dump, safe_load


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
        'chiapos_max_cores': None,
        'chiapos_max_cuda_devices': None,
        'chiapos_max_opencl_devices': None,
        'chiapos_max_gpu_devices': None,
        'chiapos_opencl_platform': None,
        'chiapos_min_gpu_log_entries': None,
        'cuda_visible_devices': None,
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
            config = safe_load(opened_config_file)
        return config

    def save_config(self, config: Dict):
        with open(self._file_path, "w") as f:
            safe_dump(config, f)
