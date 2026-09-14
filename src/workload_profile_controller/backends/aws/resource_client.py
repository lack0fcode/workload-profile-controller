import time
from collections.abc import Mapping

import boto3

from ...errors import InvalidResourceStateError, TaskTimeoutError
from .config import AwsConfig


class AwsResourceClient:
    def __init__(self, config: AwsConfig):
        session = boto3.Session(
            profile_name=config.profile,
            region_name=config.region,
        )

        self._client = session.client(
            "ec2",
            endpoint_url=config.endpoint_url,
        )

        self._operation_timeout = config.operation_timeout

    def list_instances(self):
        paginator = self._client.get_paginator(
            "describe_instances",
        )

        reservations = []

        for page in paginator.paginate():
            reservations.extend(page["Reservations"])

        return reservations

    def get_instance_state(self, instance_id: str) -> str:
        response = self._client.describe_instances(
            InstanceIds=[instance_id],
        )

        reservations = response.get("Reservations", [])

        if not isinstance(reservations, list):
            raise InvalidResourceStateError(
                f"AWS instance has no state: {instance_id}",
            )

        for reservation in reservations:
            if not isinstance(reservation, Mapping):
                continue

            instances = reservation.get("Instances", [])

            if not isinstance(instances, list):
                continue

            for instance in instances:
                if not isinstance(instance, Mapping):
                    continue

                if instance.get("InstanceId") != instance_id:
                    continue

                state = instance.get("State", {})

                if not isinstance(state, Mapping):
                    break

                state_name = state.get("Name")

                if isinstance(state_name, str):
                    return state_name

                break

        raise InvalidResourceStateError(
            f"AWS instance has no state: {instance_id}",
        )

    def start_instance(self, instance_id: str) -> None:
        self._client.start_instances(
            InstanceIds=[instance_id],
        )

        self._wait_for_state(
            instance_id=instance_id,
            desired_state="running",
            transitional_state="pending",
        )

    def stop_instance(self, instance_id: str) -> None:
        self._client.stop_instances(
            InstanceIds=[instance_id],
        )

        self._wait_for_state(
            instance_id=instance_id,
            desired_state="stopped",
            transitional_state="stopping",
        )

    def _wait_for_state(
        self,
        instance_id: str,
        desired_state: str,
        transitional_state: str,
    ) -> None:
        started_at = time.monotonic()

        while True:
            state = self.get_instance_state(instance_id)

            if state == desired_state:
                return

            if state != transitional_state:
                raise InvalidResourceStateError(
                    "AWS instance entered unexpected state: "
                    f"{instance_id}: {state}",
                )

            if (
                time.monotonic() - started_at
                >= self._operation_timeout
            ):
                raise TaskTimeoutError(
                    "AWS instance operation timed out: "
                    f"{instance_id}",
                )

            time.sleep(1.0)