from asyncio import sleep, run
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import click
from chia.cmds.cmds_util import get_wallet, cli_confirm
from chia.cmds.units import units
from chia.daemon.client import DaemonProxy
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.util.config import load_config
from chia.util.ints import uint16, uint64
from yaspin import yaspin

from foxy_gh_farmer.foundation.wallet.pool_join import get_plot_nft_not_pooling_with_foxy, join_plot_nfts_to_pool, \
    await_launcher_pool_join_completion
from foxy_gh_farmer.foundation.wallet.sync import wait_for_wallet_sync
from foxy_gh_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_gh_farmer.foxy_config_manager import FoxyConfigManager
from foxy_gh_farmer.gigahorse_launcher import ensure_daemon_running_and_unlocked, async_start
from foxy_gh_farmer.util.daemon import shutdown_daemon


@click.command("join-pool", short_help="Join your PlotNFTs to the pool")
@click.option(
    '-f',
    '--fee',
    default=Decimal(0),
    help="Fee to use for each pool join, in XCH",
    type=Decimal,
    show_default=True
)
@click.pass_context
def join_pool_cmd(ctx, fee: Decimal) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    config_path: Path = ctx.obj["config_path"]
    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    foxy_chia_config_manager.ensure_foxy_config(config_path)

    if fee >= 0.1:
        cli_confirm(f"You selected a fee of {fee} XCH, do you really want to continue? (y/n): ")

    fee_raw: uint64 = uint64(int(fee * units["chia"]))

    run(join_pool(foxy_root, config_path, fee=fee_raw))


async def join_pool(
    foxy_root: Path,
    config_path: Path,
    fee: uint64,
):
    config = load_config(foxy_root, "config.yaml")
    foxy_config_manager = FoxyConfigManager(config_path)
    foxy_config = foxy_config_manager.load_config()

    (daemon_proxy, close_daemon_on_exit) = await start_wallet(foxy_root, config, foxy_config)

    wallet_rpc = await WalletRpcClient.create(
        config["self_hostname"],
        uint16(config["wallet"]["rpc_port"]),
        foxy_root,
        config,
    )

    async def is_wallet_reachable() -> bool:
        try:
            await wallet_rpc.healthz()

            return True
        except:
            return False

    try:
        with yaspin(text="Waiting for the wallet to finish starting ..."):
            while not await is_wallet_reachable():
                await sleep(3)

        # Select wallet to sync
        await get_wallet(foxy_root, wallet_rpc, fingerprint=None)

        await wait_for_wallet_sync(wallet_rpc)
        update_foxy_config_plot_nfts_if_required(foxy_root, foxy_config, foxy_config_manager)

        plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(foxy_root)
        if len(plot_nfts_not_pooling_with_foxy) == 0:
            print("✅ All PlotNFTs are already pooling with Foxy, nothing to do")

            return

        joined_launcher_ids = await join_plot_nfts_to_pool(wallet_rpc, plot_nfts_not_pooling_with_foxy, fee=fee)
        if len(joined_launcher_ids) == 0:
            print("❌ Unable to join any of the PlotNFTs, exiting")

            return

        await wait_for_wallet_sync(wallet_rpc)

        await await_launcher_pool_join_completion(foxy_root, joined_launcher_ids)
        print("✅ Pool join completed")
        update_foxy_config_plot_nfts_if_required(foxy_root, foxy_config, foxy_config_manager)
    finally:
        wallet_rpc.close()
        await wallet_rpc.await_closed()
        await stop_wallet(daemon_proxy, close_daemon_on_exit)
        await daemon_proxy.close()


def update_foxy_config_plot_nfts_if_required(foxy_root: Path, foxy_config: Dict[str, Any], foxy_config_manager: FoxyConfigManager):
    config = load_config(foxy_root, "config.yaml")
    pool_list: Optional[List[Dict[str, Any]]] = config["pool"].get("pool_list")
    if pool_list is None:
        return
    for pool in pool_list:
        ensure_foxy_gh_farmer_client_path_removed_in_pool_url(pool)
    if pool_list == foxy_config.get("plot_nfts"):
        return
    foxy_config["plot_nfts"] = pool_list
    foxy_config_manager.save_config(foxy_config)


async def stop_wallet(daemon_proxy: DaemonProxy, close_daemon: bool):
    await daemon_proxy.stop_service("chia_wallet")

    if close_daemon:
        await shutdown_daemon(daemon_proxy)


async def start_wallet(foxy_root: Path, config: Dict[str, Any], foxy_config: Dict[str, Any]) -> Tuple[DaemonProxy, bool]:
    daemon_proxy, close_daemon_on_exit = await ensure_daemon_running_and_unlocked(foxy_root, config, foxy_config)
    assert daemon_proxy is not None

    await async_start(daemon_proxy, ["wallet"])

    return daemon_proxy, close_daemon_on_exit


def ensure_foxy_gh_farmer_client_path_removed_in_pool_url(pool: Dict[str, Any]) -> bool:
    pool_url: str = pool["pool_url"]
    if "foxypool.io" not in pool_url:
        return False
    url_parts = pool_url.split("/")
    if len(url_parts) != 4:
        return False
    url_parts.pop()
    new_pool_url = "/".join(url_parts)
    pool["pool_url"] = new_pool_url

    return True
