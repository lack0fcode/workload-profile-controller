from dataclasses import dataclass


@dataclass(frozen=True)
class TaskStatus:
    upid: str
    status: str
    exitstatus: str | None

    @property
    def is_finished(self) -> bool:
        return self.status == "stopped"

    @property
    def is_successful(self) -> bool:
        return self.is_finished and self.exitstatus == "OK"