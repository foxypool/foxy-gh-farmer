from asyncio import run
from pathlib import Path

import click
from yaspin import yaspin

from foxy_gh_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_gh_farmer.gigahorse_binary_manager import GigahorseBinaryManager


@click.command("init", short_help="Ensure the configurations and gigahorse binary are available")
@click.pass_context
def init_cmd(ctx) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    config_path: Path = ctx.obj["config_path"]

    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    foxy_chia_config_manager.ensure_foxy_config(config_path)

    with yaspin(text="Ensuring the gigahorse binary is available"):
        run(_init_gigahorse())

    print("Init done")


async def _init_gigahorse():
    binary_manager = GigahorseBinaryManager()
    await binary_manager.get_binary_directory_path()
