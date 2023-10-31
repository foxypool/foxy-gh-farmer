import asyncio
import functools
import time
from asyncio import sleep
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Callable, Awaitable

import click
from chia.cmds.cmds_util import get_wallet
from chia.daemon.client import connect_to_daemon_and_validate, DaemonProxy
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.server.outbound_message import NodeType
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.byte_types import hexstr_to_bytes
from chia.util.config import load_config
from chia.util.ints import uint64, uint16
from chia.wallet.transaction_record import TransactionRecord
from chia.wallet.util.wallet_types import WalletType
from humanize import naturaldelta
from yaspin import yaspin

from foxy_gh_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_gh_farmer.foxy_config_manager import FoxyConfigManager
from foxy_gh_farmer.gigahorse_launcher import create_start_daemon_connection, async_start, \
    ensure_daemon_keyring_is_unlocked
from foxy_gh_farmer.pool.pool_api_client import PoolApiClient, POOL_URL


@click.command("join-pool", short_help="Join your PlotNFTs to the pool")
@click.pass_context
def join_pool_cmd(ctx) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    config_path: Path = ctx.obj["config_path"]
    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    foxy_chia_config_manager.ensure_foxy_config(config_path)

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

        config = load_config(foxy_root, "config.yaml")
        plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(config)
        if len(plot_nfts_not_pooling_with_foxy) == 0:
            print("✅ All PlotNFTs are already pooling with Foxy, nothing to do")

            return

        await join_plot_nfts_to_pool(wallet_rpc, plot_nfts_not_pooling_with_foxy)

        await wait_for_wallet_sync(wallet_rpc)

        with yaspin(text="Waiting for the pool join to complete ..."):
            while len(plot_nfts_not_pooling_with_foxy) > 0:
                await sleep(15)
                config = load_config(foxy_root, "config.yaml")
                plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(config)
        print("✅ Pool join completed")
    finally:
        wallet_rpc.close()
        await wallet_rpc.await_closed()
        await stop_wallet(daemon_proxy, close_daemon_on_exit)


async def stop_wallet(daemon_proxy: DaemonProxy, close_daemon: bool):
    await daemon_proxy.stop_service("chia_wallet")

    if close_daemon:
        r = await daemon_proxy.exit()
        await daemon_proxy.close()
        if r.get("data", {}).get("success", False):
            if r["data"].get("services_stopped") is not None:
                [print(f"{service}: Stopped") for service in r["data"]["services_stopped"]]
            print("Daemon stopped")
        else:
            print(f"Stop daemon failed {r}")


async def join_plot_nfts_to_pool(wallet_client: WalletRpcClient, plot_nfts: List[Dict[str, Any]]):
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
        launcher_id = pool_wallet_info.launcher_id.hex()
        if plot_nft is None:
            print(f"❌ Could not find PlotNFT with LauncherID {launcher_id} in config.yaml, skipping")

            continue
        with yaspin(text=f"Joining PlotNFT with LauncherID {launcher_id} to the pool ...") as spinner:
            while not (await wallet_client.get_synced()):
                await sleep(5)
            try:
                await join_plot_nft_to_pool(wallet_client, pool_info, wallet_id)
                spinner.stop()
                print(f"✅ Submitted the pool join transaction for PlotNFT with LauncherID {launcher_id}")
            except Exception as e:
                spinner.stop()
                print(f"❌ Could not join PlotNFT with LauncherID {launcher_id} because an error occurred: {e}")


async def join_plot_nft_to_pool(wallet_client: WalletRpcClient, pool_info: Dict[str, Any], wallet_id: int):
    func = functools.partial(
        wallet_client.pw_join_pool,
        wallet_id,
        hexstr_to_bytes(pool_info["target_puzzle_hash"]),
        POOL_URL,
        pool_info["relative_lock_height"],
        uint64(0),
    )
    await submit_tx_with_confirmation(func, wallet_client)
    await sleep(15)


async def wait_for_wallet_sync(wallet_client: WalletRpcClient):
    with yaspin(text="Waiting for the wallet to sync ...") as spinner:
        async def update_spinner_text():
            connected_full_nodes_count = len(await wallet_client.get_connections(node_type=NodeType.FULL_NODE))
            wallet_height = await wallet_client.get_height_info()
            relative_time = "N/A"
            if connected_full_nodes_count > 0:
                try:
                    wallet_timestamp = await wallet_client.get_timestamp_for_height(wallet_height)
                    relative_time = naturaldelta(datetime.now() - datetime.fromtimestamp(float(wallet_timestamp)))
                except:
                    pass
            spinner.text = f"Waiting for the wallet to sync (peers={connected_full_nodes_count}, height={wallet_height}, {relative_time} behind) ..."

        while len(await wallet_client.get_connections(node_type=NodeType.FULL_NODE)) < 2:
            await update_spinner_text()
            await sleep(5)
        await update_spinner_text()
        await sleep(10)
        while await wallet_client.get_sync_status():
            await update_spinner_text()
            await sleep(5)
        while not (await wallet_client.get_synced()):
            await update_spinner_text()
            await sleep(5)
    print("✅ Wallet synced")


async def start_wallet(foxy_root: Path, config: Dict[str, Any], foxy_config: Dict[str, Any]) -> Tuple[DaemonProxy, bool]:
    daemon_proxy = await connect_to_daemon_and_validate(foxy_root, config, quiet=True)
    close_daemon_on_exit = False
    if daemon_proxy is None:
        daemon_proxy = await create_start_daemon_connection(foxy_root, config, foxy_config)
        close_daemon_on_exit = True
    assert daemon_proxy is not None
    await ensure_daemon_keyring_is_unlocked(daemon_proxy)

    await async_start(daemon_proxy, ["wallet"])

    return daemon_proxy, close_daemon_on_exit


def get_plot_nft_not_pooling_with_foxy(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    if config["pool"].get("pool_list") is None:
        return []

    return list(filter(lambda pool: "foxypool.io" not in pool["pool_url"], config["pool"]["pool_list"]))


async def submit_tx_with_confirmation(
    func: Callable[[], Awaitable[Dict[str, Any]]],
    wallet_client: WalletRpcClient,
) -> None:
    result = await func()
    tx_record: TransactionRecord = result["transaction"]
    start = time.time()
    while time.time() - start < 15:
        await asyncio.sleep(0.1)
        tx = await wallet_client.get_transaction(1, tx_record.name)
        if len(tx.sent_to) > 0:
            return None
