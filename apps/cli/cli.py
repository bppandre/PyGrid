import os
import json

import click

from .providers.aws import get_aws_config
from .providers.azure import get_azure_config
from .providers.gcp import get_gcp_config
from .utils import COLORS, Config, colored

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option("--output-file", default="config.json")
@pass_config
def cli(config, output_file):
    """OpenMined CLI for Infrastructure Management.

    Example:

    >>> pygrid deploy --provider aws node

    >>> pygrid deploy --provider azure network
    """
    click.echo(colored("Welcome to OpenMined PyGrid CLI!"))
    config.output_file = output_file


@cli.command()
@click.option(
    "--provider",
    prompt="Cloud Provider: ",
    default="AWS",
    type=click.Choice(["AWS", "GCP", "AZURE"], case_sensitive=False),
    help="The Cloud Provider for the deployment",
)
@click.option(
    "--app",
    prompt="PyGrid App: ",
    default="Node",
    type=click.Choice(["Node", "Network", "Worker"], case_sensitive=False),
    help="The PyGrid App to be deployed",
)
@pass_config
def deploy(config, provider, app):
    click.echo(f"Starting the deployment on {colored(provider)}...")
    config.provider = provider.lower()

    ## Get app config and arguments
    config.app = Config(name=app.lower())
    get_app_arguments(config)

    ## Deployment Keys
    config.id_key = click.prompt(
        f"Please enter a your cloud deployment {colored('id')} key",
        type=str,
        hide_input=True,
    )
    config.secret_key = click.prompt(
        f"Please enter a your cloud deployment {colored('secret')} key",
        type=str,
        hide_input=True,
    )

    ## Websockets
    if click.confirm(f"Will you need to support Websockets?"):
        if config.provider != "aws":
            config.deployment_type = "serverfull"
        elif click.confirm(f"Do you want to deploy serverless?"):
            config.deployment_type = "serverless"

    elif click.confirm(f"Do you want to deploy serverless?"):
        click.echo("we are going to serverless deployment!")
        config.deployment_type = "serverless"

    ## Prompting user to provide configuration for the selected cloud
    get_provider_config(config)
    if click.confirm(
        f"Your current configration are => {colored(config.provider.upper())}: {(vars(config)[config.provider])} \n Continue?"
    ):
        click.echo("Deploying...")


def get_provider_config(config):
    if config.provider == "aws":
        config.aws = get_aws_config()
    elif config.provider == "gcp":
        config.gcp = get_gcp_config()
    elif config.provider == "azure":
        config.azure = get_azure_config()


def get_app_arguments(config):
    if config.app.name == "node":
        config.app.id = click.prompt(
            f"PyGrid Node ID", type=str, default=os.environ.get("NODE_ID", None),
        )
        config.app.port = click.prompt(
            f"Port number of the socket.io server",
            type=str,
            default=os.environ.get("GRID_NODE_PORT", 5000),
        )
        config.app.host = click.prompt(
            f"Grid node host",
            type=str,
            default=os.environ.get("GRID_NODE_HOST", "0.0.0.0"),
        )
        config.app.network = click.prompt(
            f"Grid Network address (e.g. --network=0.0.0.0:7000)",
            type=str,
            default=os.environ.get("NETWORK", None),
        )
        config.app.num_replicas = click.prompt(
            f"Number of replicas to provide fault tolerance to model hosting",
            type=int,
            default=os.environ.get("NUM_REPLICAS", None),
        )
        config.app.start_local_db = click.prompt(
            f"Start local db (If this flag is used a SQLAlchemy DB URI is generated to use a local db)",
            type=bool,
            default=False,
        )
    elif config.app.name == "network":
        config.app.port = click.prompt(
            f"Port number of the socket.io server",
            type=str,
            default=os.environ.get("GRID_NETWORK_PORT", "7000"),
        )
        config.app.host = click.prompt(
            f"GridNerwork host",
            type=str,
            default=os.environ.get("GRID_NETWORK_HOST", "0.0.0.0"),
        )
        config.app.start_local_db = click.prompt(
            f"Start local db (If this flag is used a SQLAlchemy DB URI is generated to use a local db)",
            type=bool,
            default=False,
        )
    else:
        # TODO: Workers arguments
        pass


@cli.resultcallback()
@pass_config
def logging(config, results, **kwargs):
    click.echo(f"Writing configs to {config.output_file}")
    del config.id_key
    del config.secret_key
    with open(config.output_file, "w", encoding="utf-8") as f:
        json.dump(vars(config), f, default=lambda o: o.__dict__)