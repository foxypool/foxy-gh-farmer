from chia.daemon.client import DaemonProxy


async def shutdown_daemon(daemon_proxy: DaemonProxy, quiet: bool = False):
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
