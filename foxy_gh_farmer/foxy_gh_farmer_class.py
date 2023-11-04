from asyncio import create_task, sleep, new_event_loop, get_running_loop
from functools import partial
from logging import getLogger
from pathlib import Path
from signal import SIGINT, SIGTERM
from sys import platform
from types import FrameType
from typing import Optional, List

from chia.daemon.client import DaemonProxy
from chia.util.config import load_config
from sentry_sdk.sessions import auto_session_tracking

from foxy_gh_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_gh_farmer.foxy_config_manager import FoxyConfigManager
from foxy_gh_farmer.foxy_gh_farmer_logging import initialize_logging_with_stdout
from foxy_gh_farmer.gigahorse_launcher import ensure_daemon_running_and_unlocked, async_start
from foxy_gh_farmer.syslog_server import SyslogServer
from foxy_gh_farmer.util.daemon import shutdown_daemon
from foxy_gh_farmer.util.node_id import calculate_harvester_node_id_slug
from foxy_gh_farmer.version import version


class FoxyGhFarmer:
    _foxy_root: Path
    _config_path: Path
    _logger = getLogger("foxy_gh_farmer")
    _daemon_proxy: Optional[DaemonProxy] = None
    _is_shut_down: bool = False

    def __init__(self, foxy_root: Path, config_path: Path):
        self._foxy_root = foxy_root
        self._config_path = config_path

    async def start(self):
        foxy_chia_config_manager = FoxyChiaConfigManager(self._foxy_root)
        foxy_chia_config_manager.ensure_foxy_config(self._config_path)

        config = load_config(self._foxy_root, "config.yaml")
        initialize_logging_with_stdout(
            logging_config=config["logging"],
            root_path=self._foxy_root,
        )

        self._logger.info(f"Foxy-GH-Farmer {version} using config in {self._config_path}")

        foxy_config_manager = FoxyConfigManager(self._config_path)
        foxy_config = foxy_config_manager.load_config()

        syslog_server = SyslogServer(logging_config=config["logging"])
        syslog_task = create_task(syslog_server.run())

        self._daemon_proxy, _ = await ensure_daemon_running_and_unlocked(self._foxy_root, config, foxy_config, quiet=True)
        assert self._daemon_proxy is not None

        services_to_start: List[str] = ["farmer-only"]
        if foxy_config.get("enable_harvester") is True:
            services_to_start.append("harvester")
            self._logger.info(f"Harvester starting (id={calculate_harvester_node_id_slug(self._foxy_root, config)})")
        await async_start(self._daemon_proxy, services_to_start)

        with auto_session_tracking(session_mode="application"):
            while self._daemon_proxy is not None:
                await sleep(1)
        syslog_server.shutdown()
        await syslog_task
        self._is_shut_down = True

    async def stop(self):
        if self._daemon_proxy is None:
            return
        self._logger.info("Exiting ...")
        await shutdown_daemon(self._daemon_proxy)
        await self._daemon_proxy.close()
        self._daemon_proxy = None
        while self._is_shut_down is False:
            await sleep(0.1)

    def _accept_signal(self, signal_number: int, stack_frame: Optional[FrameType] = None) -> None:
        create_task(self.stop())

    async def setup_process_global_state(self) -> None:
        if platform == "win32" or platform == "cygwin":
            from win32api import SetConsoleCtrlHandler

            def on_exit(sig, func=None):
                new_loop = new_event_loop()
                new_loop.run_until_complete(new_loop.create_task(self.stop()))
                new_loop.stop()

            SetConsoleCtrlHandler(on_exit, True)
        else:
            loop = get_running_loop()
            loop.add_signal_handler(
                SIGINT,
                partial(self._accept_signal, signal_number=SIGINT)
            )
            loop.add_signal_handler(
                SIGTERM,
                partial(self._accept_signal, signal_number=SIGTERM)
            )
