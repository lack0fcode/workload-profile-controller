from .backend import AwsBackend
from .config_loader import load_aws_config
from .discovery import AwsDiscovery
from .resource_client import AwsResourceClient


def create_aws_backend() -> AwsBackend:
    config = load_aws_config()

    resource_client = AwsResourceClient(
        config=config,
    )

    discovery = AwsDiscovery(
        resource_client=resource_client,
    )

    return AwsBackend(
        discovery=discovery,
        resource_client=resource_client,
    )
