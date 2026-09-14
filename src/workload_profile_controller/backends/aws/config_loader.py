import os

from dotenv import load_dotenv

from .config import AwsConfig


load_dotenv()


def load_aws_config() -> AwsConfig:
    return AwsConfig(
        region=os.environ["WPC_AWS_REGION"],
        profile=os.environ.get("WPC_AWS_PROFILE"),
        endpoint_url=os.environ.get("WPC_AWS_ENDPOINT_URL"),
        timeout=float(
            os.environ.get(
                "WPC_AWS_TIMEOUT",
                "5.0",
            )
        ),
        operation_timeout=float(
            os.environ.get(
                "WPC_AWS_OPERATION_TIMEOUT",
                "120.0",
            )
        ),
    )
