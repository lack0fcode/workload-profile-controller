from dataclasses import dataclass


@dataclass(frozen=True)
class AwsConfig:
    region: str
    profile: str | None = None
    endpoint_url: str | None = None
    timeout: float = 5.0
    operation_timeout: float = 120.0
