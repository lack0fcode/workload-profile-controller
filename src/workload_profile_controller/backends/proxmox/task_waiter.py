from collections.abc import Callable
from time import sleep, time

from ...errors import TaskFailedError, TaskTimeoutError
from .task import TaskStatus


class TaskWaiter:
    def __init__(
        self,
        get_status: Callable[[str], TaskStatus],
        timeout: float = 30.0,
        sleep_fn: Callable[[float], None] = sleep,
        time_fn: Callable[[], float] = time,
    ):
        self._get_status = get_status
        self._timeout = timeout
        self._sleep = sleep_fn
        self._time = time_fn

    def wait(
        self,
        upid: str,
        interval: float = 1.0,
        timeout: float | None = None,
    ) -> TaskStatus:
        effective_timeout = (
            self._timeout
            if timeout is None
            else timeout
        )

        started_at = self._time()

        while True:
            status = self._get_status(upid)

            if status.is_finished:
                if not status.is_successful:
                    raise TaskFailedError(
                        f"Task failed: {upid}"
                    )

                return status

            elapsed = self._time() - started_at

            if elapsed >= effective_timeout:
                raise TaskTimeoutError(
                    f"Task timed out: {upid}"
                )

            self._sleep(interval)