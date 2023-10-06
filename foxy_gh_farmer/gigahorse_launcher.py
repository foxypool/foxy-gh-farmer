import asyncio
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from os.path import join
from pathlib import Path
from typing import Dict, Any, Optional, List

from chia.cmds.passphrase_funcs import get_current_passphrase
from chia.daemon.client import DaemonProxy, connect_to_daemon_and_validate
from chia.util.keychain import Keychain
from chia.util.service_groups import services_for_groups

from foxy_gh_farmer.gigahorse_binary_manager import GigahorseBinaryManager


async def launch_start_daemon(root_path: Path, foxy_config: Dict[str, Any]) -> subprocess.Popen:
    os.environ["CHIA_ROOT"] = str(root_path)
    if foxy_config.get("recompute_hosts") is not None:
        if isinstance(foxy_config["recompute_hosts"], str):
            os.environ["CHIAPOS_RECOMPUTE_HOST"] = foxy_config["recompute_hosts"]
        elif isinstance(foxy_config["recompute_hosts"], list) and len(foxy_config["recompute_hosts"]) > 0:
            os.environ["CHIAPOS_RECOMPUTE_HOST"] = ",".join(foxy_config["recompute_hosts"])
    if foxy_config.get("chiapos_max_cores") is not None:
        os.environ["CHIAPOS_MAX_CORES"] = foxy_config["chiapos_max_cores"]
    if foxy_config.get("chiapos_max_cuda_devices") is not None:
        os.environ["CHIAPOS_MAX_CUDA_DEVICES"] = foxy_config["chiapos_max_cuda_devices"]
    if foxy_config.get("chiapos_max_opencl_devices") is not None:
        os.environ["CHIAPOS_MAX_OPENCL_DEVICES"] = foxy_config["chiapos_max_opencl_devices"]
    if foxy_config.get("chiapos_max_gpu_devices") is not None:
        os.environ["CHIAPOS_MAX_GPU_DEVICES"] = foxy_config["chiapos_max_gpu_devices"]
    if foxy_config.get("chiapos_opencl_platform") is not None:
        os.environ["CHIAPOS_OPENCL_PLATFORM"] = foxy_config["chiapos_opencl_platform"]
    if foxy_config.get("chiapos_min_gpu_log_entries") is not None:
        os.environ["CHIAPOS_MIN_GPU_LOG_ENTRIES"] = foxy_config["chiapos_min_gpu_log_entries"]
    if foxy_config.get("cuda_visible_devices") is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = foxy_config["cuda_visible_devices"]

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


async def create_start_daemon_connection(
    root_path: Path,
    config: Dict[str, Any],
    foxy_config: Dict[str, Any],
) -> Optional[DaemonProxy]:
    connection = await connect_to_daemon_and_validate(root_path, config)
    if connection is None:
        print("Starting daemon")
        # launch a daemon
        process = await launch_start_daemon(root_path, foxy_config)
        # give the daemon a chance to start up
        if process.stdout:
            process.stdout.readline()
        await asyncio.sleep(1)
        # it prints "daemon: listening"
        connection = await connect_to_daemon_and_validate(root_path, config)
    if connection:
        passphrase = None
        if await connection.is_keyring_locked():
            passphrase = Keychain.get_cached_master_passphrase()
            if passphrase is None or not Keychain.master_passphrase_is_valid(passphrase):
                with ThreadPoolExecutor(max_workers=1, thread_name_prefix="get_current_passphrase") as executor:
                    passphrase = await asyncio.get_running_loop().run_in_executor(executor, get_current_passphrase)

        if passphrase:
            print("Unlocking daemon keyring")
            await connection.unlock_keyring(passphrase)

        return connection
    return None


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
