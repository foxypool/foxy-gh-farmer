from asyncio import sleep
from logging import getLogger

from foxy_gh_farmer.cmds.join_pool import join_pool_cmd
from foxy_gh_farmer.foxy_gh_farmer_logging import initialize_logging_with_stdout
from foxy_gh_farmer.gigahorse_launcher import create_start_daemon_connection, async_start

from chia.cmds.keys import keys_cmd
from chia.cmds.passphrase import passphrase_cmd
from chia.cmds.plots import plots_cmd
from chia.daemon.client import DaemonProxy

import asyncio
import functools
import os
import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Optional, List

import click
import pkg_resources
from chia.server.start_service import async_run

from chia.util.config import load_config

from foxy_gh_farmer.cmds.farm_summary import summary_cmd
from foxy_gh_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_gh_farmer.foxy_config_manager import FoxyConfigManager
from foxy_gh_farmer.syslog_server import setup_syslog_server

version = pkg_resources.require("foxy-gh-farmer")[0].version


class FoxyFarmer:
    _foxy_root: Path
    _config_path: Path
    _logger = getLogger("main")
    _daemon_proxy: Optional[DaemonProxy] = None

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

        asyncio.create_task(setup_syslog_server(logging_config=config["logging"]))

        self._daemon_proxy = await create_start_daemon_connection(self._foxy_root, config, foxy_config)
        assert self._daemon_proxy is not None

        services_to_start: List[str] = ["farmer-only"]
        if foxy_config.get("enable_harvester") is True:
            services_to_start.append("harvester")
        await async_start(self._daemon_proxy, services_to_start)

        while self._daemon_proxy is not None:
            await sleep(1)

    async def stop(self):
        if self._daemon_proxy is None:
            return
        self._logger.info("Exiting ...")
        r = await self._daemon_proxy.exit()
        await self._daemon_proxy.close()
        if r.get("data", {}).get("success", False):
            if r["data"].get("services_stopped") is not None:
                [print(f"{service}: Stopped") for service in r["data"]["services_stopped"]]
            print("Daemon stopped")
        else:
            print(f"Stop daemon failed {r}")
        self._daemon_proxy = None

    def _accept_signal(self, signal_number: int, stack_frame: Optional[FrameType] = None) -> None:
        asyncio.create_task(self.stop())

    async def setup_process_global_state(self) -> None:
        if sys.platform == "win32" or sys.platform == "cygwin":
            # pylint: disable=E1101
            # signal.signal(signal.SIGBREAK, self._accept_signal)
            # signal.signal(signal.SIGINT, self._accept_signal)
            # signal.signal(signal.SIGTERM, self._accept_signal)
            from win32api import SetConsoleCtrlHandler

            def on_exit(sig, func=None):
                loop = asyncio.new_event_loop()
                loop.run_until_complete(loop.create_task(self.stop()))
                loop.stop()

            SetConsoleCtrlHandler(on_exit, True)
        else:
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(
                signal.SIGINT,
                functools.partial(self._accept_signal, signal_number=signal.SIGINT)
            )
            loop.add_signal_handler(
                signal.SIGTERM,
                functools.partial(self._accept_signal, signal_number=signal.SIGTERM)
            )


async def run_foxy_gh_farmer(foxy_root: Path, config_path: Path):
    foxy_gh_farmer = FoxyFarmer(foxy_root, config_path)
    await foxy_gh_farmer.setup_process_global_state()
    await foxy_gh_farmer.start()


@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"])
)
@click.option(
    '-c',
    '--config',
    default='foxy-gh-farmer.yaml',
    help="Config file path",
    type=click.Path(),
    show_default=True
)
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj["root_path"] = Path(os.path.expanduser(os.getenv("FOXY_GH_ROOT", "~/.foxy-gh-farmer/mainnet"))).resolve()
    ctx.obj["config_path"] = Path(config).resolve()
    if ctx.invoked_subcommand is None:
        ctx.forward(run_cmd)


@cli.command("run", short_help="Run foxy-gh-farmer, can be omitted")
@click.pass_context
def run_cmd(ctx, config):
    async_run(run_foxy_gh_farmer(ctx.obj["root_path"], ctx.obj["config_path"]))


cli.add_command(summary_cmd)
cli.add_command(join_pool_cmd)
cli.add_command(keys_cmd)
cli.add_command(plots_cmd)
cli.add_command(passphrase_cmd)


def main() -> None:
    cli()


if __name__ == '__main__':
    main()
