from workload_profile_controller.backends.aws.config import AwsConfig


def test_aws_config_can_be_created():
    config = AwsConfig(
        region="us-east-1",
    )

    assert config.region == "us-east-1"
    assert config.profile is None
    assert config.endpoint_url is None
    assert config.timeout == 5.0
    assert config.operation_timeout == 120.0


def test_aws_config_accepts_custom_options():
    config = AwsConfig(
        region="us-west-2",
        profile="localstack",
        endpoint_url="http://localhost.localstack.cloud:4566",
        timeout=10.0,
        operation_timeout=60.0,
    )

    assert config.region == "us-west-2"
    assert config.profile == "localstack"
    assert config.endpoint_url == "http://localhost.localstack.cloud:4566"
    assert config.timeout == 10.0
    assert config.operation_timeout == 60.0
