from unittest.mock import MagicMock

import boto3
import pytest

from workload_profile_controller.backends.aws.config import AwsConfig
from workload_profile_controller.backends.aws.resource_client import (
    AwsResourceClient,
)
from workload_profile_controller.errors import (
    InvalidResourceStateError,
    TaskTimeoutError,
)


def make_config(**kwargs):
    values = {
        "region": "us-east-1",
        "profile": "localstack",
        "endpoint_url": "http://localhost.localstack.cloud:4566",
    }

    values.update(kwargs)

    return AwsConfig(**values)


def make_client(monkeypatch, **config_kwargs):
    session = MagicMock()
    ec2_client = MagicMock()

    session.client.return_value = ec2_client

    monkeypatch.setattr(
        boto3,
        "Session",
        lambda **kwargs: session,
    )

    client = AwsResourceClient(make_config(**config_kwargs))

    return client, session, ec2_client


def test_aws_resource_client_creates_ec2_client(monkeypatch):
    client, session, ec2_client = make_client(monkeypatch)

    assert client._client is ec2_client

    session.client.assert_called_once_with(
        "ec2",
        endpoint_url="http://localhost.localstack.cloud:4566",
    )


def test_list_instances_returns_reservations_from_all_pages(monkeypatch):
    client, _, ec2_client = make_client(monkeypatch)

    paginator = MagicMock()

    paginator.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-first",
                            "State": {
                                "Name": "running",
                            },
                        },
                    ],
                },
            ],
        },
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-second",
                            "State": {
                                "Name": "stopped",
                            },
                        },
                    ],
                },
            ],
        },
    ]

    ec2_client.get_paginator.return_value = paginator

    reservations = client.list_instances()

    assert reservations == [
        {
            "Instances": [
                {
                    "InstanceId": "i-first",
                    "State": {
                        "Name": "running",
                    },
                },
            ],
        },
        {
            "Instances": [
                {
                    "InstanceId": "i-second",
                    "State": {
                        "Name": "stopped",
                    },
                },
            ],
        },
    ]

    ec2_client.get_paginator.assert_called_once_with(
        "describe_instances",
    )

    paginator.paginate.assert_called_once_with()


def test_get_instance_state_returns_running(monkeypatch):
    client, _, ec2_client = make_client(monkeypatch)

    ec2_client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-running",
                        "State": {
                            "Name": "running",
                        },
                    },
                ],
            },
        ],
    }

    state = client.get_instance_state("i-running")

    assert state == "running"

    ec2_client.describe_instances.assert_called_once_with(
        InstanceIds=["i-running"],
    )


def test_get_instance_state_returns_stopped(monkeypatch):
    client, _, ec2_client = make_client(monkeypatch)

    ec2_client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-stopped",
                        "State": {
                            "Name": "stopped",
                        },
                    },
                ],
            },
        ],
    }

    state = client.get_instance_state("i-stopped")

    assert state == "stopped"


def test_get_instance_state_returns_pending(monkeypatch):
    client, _, ec2_client = make_client(monkeypatch)

    ec2_client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-pending",
                        "State": {
                            "Name": "pending",
                        },
                    },
                ],
            },
        ],
    }

    state = client.get_instance_state("i-pending")

    assert state == "pending"


def test_get_instance_state_returns_stopping(monkeypatch):
    client, _, ec2_client = make_client(monkeypatch)

    ec2_client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-stopping",
                        "State": {
                            "Name": "stopping",
                        },
                    },
                ],
            },
        ],
    }

    state = client.get_instance_state("i-stopping")

    assert state == "stopping"


def test_get_instance_state_raises_when_instance_is_missing(monkeypatch):
    client, _, ec2_client = make_client(monkeypatch)

    ec2_client.describe_instances.return_value = {
        "Reservations": [],
    }

    with pytest.raises(
        InvalidResourceStateError,
        match="AWS instance has no state",
    ):
        client.get_instance_state("i-missing")


def test_start_instance_starts_instance_and_waits_for_running(
    monkeypatch,
):
    client, _, ec2_client = make_client(monkeypatch)

    ec2_client.start_instances.return_value = {
        "StartingInstances": [
            {
                "InstanceId": "i-start",
                "CurrentState": {
                    "Name": "pending",
                },
                "PreviousState": {
                    "Name": "stopped",
                },
            },
        ],
    }

    states = iter(["pending", "running"])

    monkeypatch.setattr(
        client,
        "get_instance_state",
        lambda instance_id: next(states),
    )

    monkeypatch.setattr(
        "workload_profile_controller.backends.aws.resource_client.time.sleep",
        lambda _: None,
    )

    client.start_instance("i-start")

    ec2_client.start_instances.assert_called_once_with(
        InstanceIds=["i-start"],
    )


def test_stop_instance_stops_instance_and_waits_for_stopped(
    monkeypatch,
):
    client, _, ec2_client = make_client(monkeypatch)

    ec2_client.stop_instances.return_value = {
        "StoppingInstances": [
            {
                "InstanceId": "i-stop",
                "CurrentState": {
                    "Name": "stopping",
                },
                "PreviousState": {
                    "Name": "running",
                },
            },
        ],
    }

    states = iter(["stopping", "stopped"])

    monkeypatch.setattr(
        client,
        "get_instance_state",
        lambda instance_id: next(states),
    )

    monkeypatch.setattr(
        "workload_profile_controller.backends.aws.resource_client.time.sleep",
        lambda _: None,
    )

    client.stop_instance("i-stop")

    ec2_client.stop_instances.assert_called_once_with(
        InstanceIds=["i-stop"],
    )


def test_start_instance_raises_when_instance_enters_unexpected_state(
    monkeypatch,
):
    client, _, ec2_client = make_client(monkeypatch)

    ec2_client.start_instances.return_value = {
        "StartingInstances": [],
    }

    monkeypatch.setattr(
        client,
        "get_instance_state",
        lambda instance_id: "terminated",
    )

    with pytest.raises(
        InvalidResourceStateError,
        match="AWS instance entered unexpected state",
    ):
        client.start_instance("i-start")


def test_stop_instance_raises_when_instance_enters_unexpected_state(
    monkeypatch,
):
    client, _, ec2_client = make_client(monkeypatch)

    ec2_client.stop_instances.return_value = {
        "StoppingInstances": [],
    }

    monkeypatch.setattr(
        client,
        "get_instance_state",
        lambda instance_id: "terminated",
    )

    with pytest.raises(
        InvalidResourceStateError,
        match="AWS instance entered unexpected state",
    ):
        client.stop_instance("i-stop")


def test_start_instance_times_out(monkeypatch):
    client, _, ec2_client = make_client(
        monkeypatch,
        operation_timeout=2.0,
    )

    ec2_client.start_instances.return_value = {
        "StartingInstances": [],
    }

    monkeypatch.setattr(
        client,
        "get_instance_state",
        lambda instance_id: "pending",
    )

    times = iter([0.0, 1.0, 2.0])

    monkeypatch.setattr(
        "workload_profile_controller.backends.aws.resource_client.time.monotonic",
        lambda: next(times),
    )

    monkeypatch.setattr(
        "workload_profile_controller.backends.aws.resource_client.time.sleep",
        lambda _: None,
    )

    with pytest.raises(
        TaskTimeoutError,
        match="AWS instance operation timed out",
    ):
        client.start_instance("i-timeout")


def test_stop_instance_times_out(monkeypatch):
    client, _, ec2_client = make_client(
        monkeypatch,
        operation_timeout=2.0,
    )

    ec2_client.stop_instances.return_value = {
        "StoppingInstances": [],
    }

    monkeypatch.setattr(
        client,
        "get_instance_state",
        lambda instance_id: "stopping",
    )

    times = iter([0.0, 1.0, 2.0])

    monkeypatch.setattr(
        "workload_profile_controller.backends.aws.resource_client.time.monotonic",
        lambda: next(times),
    )

    monkeypatch.setattr(
        "workload_profile_controller.backends.aws.resource_client.time.sleep",
        lambda _: None,
    )

    with pytest.raises(
        TaskTimeoutError,
        match="AWS instance operation timed out",
    ):
        client.stop_instance("i-timeout")