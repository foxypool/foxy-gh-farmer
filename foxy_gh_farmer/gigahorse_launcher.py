import asyncio
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from os.path import join
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from chia.cmds.passphrase_funcs import get_current_passphrase
from chia.daemon.client import DaemonProxy, connect_to_daemon_and_validate
from chia.util.keychain import Keychain
from chia.util.service_groups import services_for_groups

from foxy_gh_farmer.gigahorse_binary_manager import GigahorseBinaryManager
from foxy_gh_farmer.util.daemon import shutdown_daemon


async def launch_start_daemon(root_path: Path, foxy_config: Dict[str, Any]) -> subprocess.Popen:
    os.environ["CHIA_ROOT"] = str(root_path)
    if foxy_config.get("recompute_hosts") is not None:
        if isinstance(foxy_config["recompute_hosts"], str):
            os.environ["CHIAPOS_RECOMPUTE_HOST"] = foxy_config["recompute_hosts"]
        elif isinstance(foxy_config["recompute_hosts"], list) and len(foxy_config["recompute_hosts"]) > 0:
            os.environ["CHIAPOS_RECOMPUTE_HOST"] = ",".join(foxy_config["recompute_hosts"])
    if foxy_config.get("recompute_connect_timeout") is not None:
        os.environ["CHIAPOS_RECOMPUTE_CONNECT_TIMEOUT"] = str(foxy_config["recompute_connect_timeout"])
    if foxy_config.get("recompute_retry_interval") is not None:
        os.environ["CHIAPOS_RECOMPUTE_RETRY_INTERVAL"] = str(foxy_config["recompute_retry_interval"])
    if foxy_config.get("chiapos_max_cores") is not None:
        os.environ["CHIAPOS_MAX_CORES"] = str(foxy_config["chiapos_max_cores"])
    if foxy_config.get("chiapos_max_cuda_devices") is not None:
        os.environ["CHIAPOS_MAX_CUDA_DEVICES"] = str(foxy_config["chiapos_max_cuda_devices"])
    if foxy_config.get("chiapos_max_opencl_devices") is not None:
        os.environ["CHIAPOS_MAX_OPENCL_DEVICES"] = str(foxy_config["chiapos_max_opencl_devices"])
    if foxy_config.get("chiapos_max_gpu_devices") is not None:
        os.environ["CHIAPOS_MAX_GPU_DEVICES"] = str(foxy_config["chiapos_max_gpu_devices"])
    if foxy_config.get("chiapos_opencl_platform") is not None:
        os.environ["CHIAPOS_OPENCL_PLATFORM"] = str(foxy_config["chiapos_opencl_platform"])
    if foxy_config.get("chiapos_min_gpu_log_entries") is not None:
        os.environ["CHIAPOS_MIN_GPU_LOG_ENTRIES"] = str(foxy_config["chiapos_min_gpu_log_entries"])
    if foxy_config.get("cuda_visible_devices") is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(foxy_config["cuda_visible_devices"])

    creationflags = 0
    chia_binary_name = "chia.bin"
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        chia_binary_name = "chia.exe"

    binary_manager = GigahorseBinaryManager()
    gigahorse_path = await binary_manager.get_binary_directory_path()

    process = subprocess.Popen(
        [join(gigahorse_path, chia_binary_name), "run_daemon", "--wait-for-unlock"],
        encoding="utf-8",
        cwd=gigahorse_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
    )

    return process


async def ensure_daemon_keyring_is_unlocked(daemon_proxy: DaemonProxy):
    passphrase = None
    if await daemon_proxy.is_keyring_locked():
        passphrase = Keychain.get_cached_master_passphrase()
        if passphrase is None or not Keychain.master_passphrase_is_valid(passphrase):
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix="get_current_passphrase") as executor:
                passphrase = await asyncio.get_running_loop().run_in_executor(executor, get_current_passphrase)

    if passphrase:
        print("Unlocking daemon keyring")
        await daemon_proxy.unlock_keyring(passphrase)


async def ensure_daemon_running_and_unlocked(
    root_path: Path,
    config: Dict[str, Any],
    foxy_config: Dict[str, Any],
    quiet: bool = False,
) -> Tuple[Optional[DaemonProxy], bool]:
    did_start_daemon = False
    daemon_proxy = await connect_to_daemon_and_validate(root_path, config, quiet=True)
    if daemon_proxy is None:
        if not quiet:
            print("Starting daemon")
        # launch a daemon
        process = await launch_start_daemon(root_path, foxy_config)
        did_start_daemon = True
        # give the daemon a chance to start up
        if process.stdout:
            process.stdout.readline()
        await asyncio.sleep(1)
        # it prints "daemon: listening"
        daemon_proxy = await connect_to_daemon_and_validate(root_path, config, quiet=quiet)
    if daemon_proxy:
        try:
            await ensure_daemon_keyring_is_unlocked(daemon_proxy)
        except KeyboardInterrupt:
            if did_start_daemon:
                await shutdown_daemon(daemon_proxy, quiet=quiet)
            await daemon_proxy.close()

            raise

        return daemon_proxy, did_start_daemon
    return None, did_start_daemon


async def async_start(daemon_proxy: DaemonProxy, group: List[str]) -> None:
    for service in services_for_groups(group):
        if await daemon_proxy.is_running(service_name=service):
            continue
        print(f"{service}: ", end="", flush=True)
        msg = await daemon_proxy.start_service(service_name=service)
        success = msg and msg["data"]["success"]

        if success is True:
            print("started")
        else:
            error = "no response"
            if msg:
                error = msg["data"]["error"]
            print(f"{service} failed to start. Error: {error}")
