from asyncio import sleep, run
from logging import getLogger
from pathlib import Path
from typing import Dict, Any, Optional

import click
from chia.daemon.keychain_proxy import connect_to_keychain_and_validate, KeychainProxy
from chia.util.config import load_config

from foxy_gh_farmer.foundation.keychain.generate_login_links import generate_login_links
from foxy_gh_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_gh_farmer.foxy_config_manager import FoxyConfigManager
from foxy_gh_farmer.gigahorse_launcher import ensure_daemon_running_and_unlocked
from foxy_gh_farmer.util.daemon import shutdown_daemon


@click.command("auth", short_help="Authenticate your Launcher Ids on the pool")
@click.pass_context
def authenticate_cmd(ctx) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    config_path: Path = ctx.obj["config_path"]
    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    foxy_chia_config_manager.ensure_foxy_config(config_path)

    config = load_config(foxy_root, "config.yaml")
    foxy_config_manager = FoxyConfigManager(config_path)
    foxy_config = foxy_config_manager.load_config()

    run(authenticate(foxy_root, config, foxy_config))


async def authenticate(
    foxy_root: Path,
    config: Dict[str, Any],
    foxy_config: Dict[str, Any],
):
    pool_list = config["pool"].get("pool_list", [])
    if pool_list is None or len(pool_list) == 0:
        print("No PlotNFTs found in your config, did you join the pool via the join-pool command yet?")

        return

    logger = getLogger("auth")
    daemon_proxy, close_daemon_on_exit = await ensure_daemon_running_and_unlocked(foxy_root, config, foxy_config)
    assert daemon_proxy is not None

    keychain_proxy: Optional[KeychainProxy] = None
    try:
        keychain_proxy = await connect_to_keychain_and_validate(foxy_root, logger)
        assert keychain_proxy is not None
        login_links = await generate_login_links(keychain_proxy, pool_list)
        for launcher_id, login_link in login_links:
            print()
            print(f"Launcher Id: {launcher_id}")
            print(f" Login Link: {login_link}")
    finally:
        if keychain_proxy is not None:
            await keychain_proxy.close()
            await sleep(0.5)
        if close_daemon_on_exit:
            await shutdown_daemon(daemon_proxy, quiet=True)
        await daemon_proxy.close()
