from pathlib import Path

import click
from chia.cmds.keys import keys_cmd
from chia.cmds.passphrase import passphrase_cmd

from foxy_gh_farmer.cmds.farm_summary import summary_cmd
from foxy_gh_farmer.cmds.authenticate import authenticate_cmd
from foxy_gh_farmer.cmds.init import init_cmd
from foxy_gh_farmer.cmds.join_pool import join_pool_cmd
from foxy_gh_farmer.error_reporting import close_sentry
from foxy_gh_farmer.util.root_path import get_root_path
from foxy_gh_farmer.version import version


async def run_foxy_gh_farmer(foxy_root: Path, config_path: Path):
    from foxy_gh_farmer.foxy_gh_farmer_class import FoxyGhFarmer
    foxy_gh_farmer = FoxyGhFarmer(foxy_root, config_path)
    await foxy_gh_farmer.setup_process_global_state()
    try:
        await foxy_gh_farmer.start()
    finally:
        close_sentry()


@click.group(
    help=f"\n======= Foxy-GH-Farmer {version} =======\n",
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
@click.option(
    '-r',
    '--root-path',
    default=get_root_path(),
    help="Chia root path",
    type=click.Path(),
    show_default=True
)
@click.version_option(version=version, message="Foxy-GH-Farmer %(version)s")
@click.pass_context
def cli(ctx, config, root_path):
    ctx.ensure_object(dict)
    ctx.obj["root_path"] = Path(root_path).resolve()
    ctx.obj["config_path"] = Path(config).resolve()
    if ctx.invoked_subcommand is None:
        ctx.forward(run_cmd)


@cli.command("run", short_help="Run foxy-gh-farmer, can be omitted")
@click.pass_context
def run_cmd(ctx, config = None, root_path = None):
    from chia.server.start_service import async_run
    async_run(run_foxy_gh_farmer(ctx.obj["root_path"], ctx.obj["config_path"]))


cli.add_command(summary_cmd)
cli.add_command(join_pool_cmd)
cli.add_command(authenticate_cmd)
cli.add_command(keys_cmd)
cli.add_command(passphrase_cmd)
cli.add_command(init_cmd)


def main() -> None:
    cli()


if __name__ == '__main__':
    main()
