import asyncio
import functools
import os
from asyncio import sleep
from pathlib import Path
from typing import Dict, Any, List, Tuple

import click
from chia.cmds.cmds_util import get_any_service_client, get_wallet
from chia.cmds.plotnft_funcs import submit_tx_with_confirmation
from chia.daemon.client import connect_to_daemon_and_validate, DaemonProxy
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.server.outbound_message import NodeType
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.byte_types import hexstr_to_bytes
from chia.util.config import load_config
from chia.util.ints import uint64
from chia.wallet.util.wallet_types import WalletType
from yaspin import yaspin

from foxy_gh_farmer.foxy_config_manager import FoxyConfigManager
from foxy_gh_farmer.gigahorse_launcher import create_start_daemon_connection, async_start
from foxy_gh_farmer.pool.pool_api_client import PoolApiClient, POOL_URL


@click.command("join-pool", short_help="Join your PlotNFTs to the pool")
@click.pass_context
def join_pool_cmd(ctx) -> None:
    foxy_root: Path = Path(os.path.expanduser(os.getenv("FOXY_GH_ROOT", "~/.foxy-gh-farmer/mainnet"))).resolve()
    if not foxy_root.exists():
        print("No config found, please start foxy-gh-farmer at least once before joining the pool!")

        return

    config = load_config(foxy_root, "config.yaml")
    foxy_config_manager = FoxyConfigManager(ctx.obj["config_path"])
    foxy_config = foxy_config_manager.load_config()

    asyncio.run(join_pool(foxy_root, config, foxy_config))


async def join_pool(
    foxy_root: Path,
    config: Dict[str, Any],
    foxy_config: Dict[str, Any],
):
    (daemon_proxy, close_daemon_on_exit) = await start_wallet(foxy_root, config, foxy_config)

    with yaspin(text="Waiting for the wallet to finish starting ..."):
        await sleep(5)

    async with get_any_service_client(WalletRpcClient, root_path=foxy_root) as (wallet_client, _):
        assert wallet_client is not None

        fingerprint = await get_wallet(foxy_root, wallet_client, fingerprint=None)

        await wait_for_wallet_sync(wallet_client)

        config = load_config(foxy_root, "config.yaml")
        plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(config)
        if len(plot_nfts_not_pooling_with_foxy) == 0:
            print("✅ All PlotNFTs are already pooling with Foxy, nothing to do")
            await stop_wallet(daemon_proxy, close_daemon_on_exit)

            return

        await join_plot_nfts_to_pool(wallet_client, plot_nfts_not_pooling_with_foxy, fingerprint)

        await wait_for_wallet_sync(wallet_client)

        with yaspin(text="Waiting for the pool join to complete ..."):
            while len(plot_nfts_not_pooling_with_foxy) > 0:
                await sleep(15)
                config = load_config(foxy_root, "config.yaml")
                plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(config)
        print("✅ Pool join completed")

    await stop_wallet(daemon_proxy, close_daemon_on_exit)


async def stop_wallet(daemon_proxy: DaemonProxy, close_daemon: bool):
    await daemon_proxy.stop_service("wallet")

    if close_daemon:
        r = await daemon_proxy.exit()
        await daemon_proxy.close()
        if r.get("data", {}).get("success", False):
            if r["data"].get("services_stopped") is not None:
                [print(f"{service}: Stopped") for service in r["data"]["services_stopped"]]
            print("Daemon stopped")
        else:
            print(f"Stop daemon failed {r}")


async def join_plot_nfts_to_pool(wallet_client: WalletRpcClient, plot_nfts: List[Dict[str, Any]], fingerprint: int):
    plot_nfts_by_launcher_id: Dict[bytes32, Dict[str, Any]] = {
        bytes32.from_hexstr(plot_nft["launcher_id"]): plot_nft
        for plot_nft in plot_nfts
    }

    pool_api_client = PoolApiClient()
    with yaspin(text="Fetching latest pool info ..."):
        pool_info = await pool_api_client.get_pool_info()

    with yaspin(text="Fetching PlotNFT wallets ..."):
        pooling_wallets = await wallet_client.get_wallets(wallet_type=WalletType.POOLING_WALLET)
    for pool_wallet in pooling_wallets:
        wallet_id = pool_wallet["id"]
        pool_wallet_info, _ = await wallet_client.pw_status(wallet_id)
        plot_nft = plot_nfts_by_launcher_id.get(pool_wallet_info.launcher_id)
        if plot_nft is None:
            print(f"Could not find PlotNFT for LauncherID {pool_wallet_info.launcher_id.hex()} in config.yaml, skipping")
            continue
        with yaspin(text=f"Joining PlotNFT with LauncherID {pool_wallet_info.launcher_id.hex()} to the pool ..."):
            await join_plot_nft_to_pool(wallet_client, pool_info, wallet_id, fingerprint)


async def join_plot_nft_to_pool(wallet_client: WalletRpcClient, pool_info: Dict[str, Any], wallet_id: int, fingerprint: int):
    func = functools.partial(
        wallet_client.pw_join_pool,
        wallet_id,
        hexstr_to_bytes(pool_info["target_puzzle_hash"]),
        POOL_URL,
        pool_info["relative_lock_height"],
        uint64(0),
    )
    await submit_tx_with_confirmation("", False, func, wallet_client, fingerprint, wallet_id)
    await sleep(15)


async def wait_for_wallet_sync(wallet_client: WalletRpcClient):
    with yaspin(text="Waiting for the wallet to sync ..."):
        while len(await wallet_client.get_connections(node_type=NodeType.FULL_NODE)) < 2:
            await sleep(5)
        await sleep(10)
        while await wallet_client.get_sync_status():
            await sleep(5)
        while not (await wallet_client.get_synced()):
            await sleep(5)
    print("✅ Wallet synced")


async def start_wallet(foxy_root: Path, config: Dict[str, Any], foxy_config: Dict[str, Any]) -> Tuple[DaemonProxy, bool]:
    daemon_proxy = await connect_to_daemon_and_validate(foxy_root, config, quiet=True)
    close_daemon_on_exit = False
    if daemon_proxy is None:
        daemon_proxy = await create_start_daemon_connection(foxy_root, config, foxy_config)
        close_daemon_on_exit = True
    assert daemon_proxy is not None

    await async_start(daemon_proxy, ["wallet"])

    return daemon_proxy, close_daemon_on_exit


def get_plot_nft_not_pooling_with_foxy(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    if config["pool"].get("pool_list") is None:
        return []

    return list(filter(lambda pool: "foxypool.io" not in pool["pool_url"], config["pool"]["pool_list"]))
