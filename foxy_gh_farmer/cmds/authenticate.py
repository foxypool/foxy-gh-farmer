import asyncio
from asyncio import sleep
from logging import getLogger
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import click
from blspy import G1Element, G2Element, AugSchemeMPL
from chia.daemon.client import connect_to_daemon_and_validate, DaemonProxy
from chia.daemon.keychain_proxy import connect_to_keychain_and_validate, KeychainProxy
from chia.protocols.pool_protocol import get_current_authentication_token, AuthenticationPayload
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.byte_types import hexstr_to_bytes
from chia.util.config import load_config
from chia.util.hash import std_hash
from chia.wallet.derive_keys import find_authentication_sk

from foxy_gh_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_gh_farmer.foxy_config_manager import FoxyConfigManager
from foxy_gh_farmer.gigahorse_launcher import create_start_daemon_connection, \
    ensure_daemon_keyring_is_unlocked
from foxy_gh_farmer.pool.pool_api_client import PoolApiClient


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

    asyncio.run(authenticate(foxy_root, config, foxy_config))


async def authenticate(
    foxy_root: Path,
    config: Dict[str, Any],
    foxy_config: Dict[str, Any],
):
    pool_list = config["pool"].get("pool_list", [])
    if len(pool_list) == 0:
        print("No PlotNFTs found in your config, did you join the pool via the join-pool command yet?")

        return

    logger = getLogger("auth")
    (daemon_proxy, close_daemon_on_exit) = await ensure_daemon_running_and_unlocked(foxy_root, config, foxy_config)

    keychain_proxy: Optional[KeychainProxy] = None
    try:
        keychain_proxy = await connect_to_keychain_and_validate(foxy_root, logger)
        assert keychain_proxy is not None
        all_root_sks = [sk for sk, _ in await keychain_proxy.get_all_private_keys()]

        for pool in pool_list:
            launcher_id = pool["launcher_id"]
            if pool.get("pool_url", "") == "":
                # Skip solo PlotNFT
                continue

            owner_public_key = G1Element.from_bytes(hexstr_to_bytes(pool["owner_public_key"]))
            authentication_sk = find_authentication_sk(all_root_sks, owner_public_key)
            if authentication_sk is None:
                print(f"The key for Launcher Id {launcher_id} does not seem to be added to this system yet, skipping ...")

                continue
            pool_url = pool["pool_url"]
            pool_api_client = PoolApiClient(pool_url=pool_url)
            pool_info = await pool_api_client.get_pool_info()
            authentication_token_timeout = pool_info["authentication_token_timeout"]
            authentication_token = get_current_authentication_token(authentication_token_timeout)
            message: bytes32 = std_hash(
                AuthenticationPayload(
                    "get_login",
                    bytes32.from_hexstr(launcher_id),
                    bytes32.from_hexstr(pool["target_puzzle_hash"]),
                    authentication_token,
                )
            )
            signature: G2Element = AugSchemeMPL.sign(authentication_sk, message)
            login_link = f"{pool_url}/login?launcher_id={launcher_id}&authentication_token={authentication_token}&signature={bytes(signature).hex()}"

            print()
            print(f"Launcher Id: {launcher_id}")
            print(f" Login Link: {login_link}")
    finally:
        if keychain_proxy is not None:
            await keychain_proxy.close()
            await sleep(0.5)
        if close_daemon_on_exit:
            await stop_daemon(daemon_proxy, quiet=True)


async def stop_daemon(daemon_proxy: DaemonProxy, quiet: bool = False):
    r = await daemon_proxy.exit()
    await daemon_proxy.close()
    if quiet:
        return
    if r.get("data", {}).get("success", False):
        if r["data"].get("services_stopped") is not None:
            [print(f"{service}: Stopped") for service in r["data"]["services_stopped"]]
        print("Daemon stopped")
    else:
        print(f"Stop daemon failed {r}")


async def ensure_daemon_running_and_unlocked(
    foxy_root: Path,
    config: Dict[str, Any],
    foxy_config: Dict[str, Any],
    quiet: bool = False,
) -> Tuple[DaemonProxy, bool]:
    daemon_proxy = await connect_to_daemon_and_validate(foxy_root, config, quiet=True)
    close_daemon_on_exit = False
    if daemon_proxy is None:
        daemon_proxy = await create_start_daemon_connection(foxy_root, config, foxy_config, quiet=quiet)
        close_daemon_on_exit = True
    assert daemon_proxy is not None
    await ensure_daemon_keyring_is_unlocked(daemon_proxy)

    return daemon_proxy, close_daemon_on_exit
