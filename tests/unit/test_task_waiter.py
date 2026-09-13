import pytest

from workload_profile_controller.backends.proxmox.task import TaskStatus
from workload_profile_controller.backends.proxmox.task_waiter import TaskWaiter
from workload_profile_controller.errors import TaskFailedError, TaskTimeoutError


def test_task_waiter_accepts_status_function():
    statuses = []

    def get_status(upid):
        return statuses.pop(0)

    waiter = TaskWaiter(
        get_status=get_status,
    )

    assert waiter._get_status is get_status


def test_task_waiter_accepts_custom_sleep_function():
    def get_status(upid):
        return TaskStatus(
            upid=upid,
            status="running",
            exitstatus=None,
        )

    def fake_sleep(seconds):
        pass

    waiter = TaskWaiter(
        get_status=get_status,
        sleep_fn=fake_sleep,
    )

    assert waiter._get_status is get_status
    assert waiter._sleep is fake_sleep

def test_task_waiter_returns_immediately_when_task_is_finished():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000001",
        status="stopped",
        exitstatus="OK",
    )

    calls = []

    def get_status(upid):
        calls.append(upid)
        return task

    def fake_sleep(seconds):
        raise AssertionError("sleep should not be called")

    waiter = TaskWaiter(
        get_status=get_status,
        sleep_fn=fake_sleep,
    )

    result = waiter.wait(task.upid)

    assert result == task
    assert calls == [task.upid]


def test_task_waiter_polls_until_task_is_finished():
    running = TaskStatus(
        upid="UPID:pve-node-01:00000001",
        status="running",
        exitstatus=None,
    )

    finished = TaskStatus(
        upid="UPID:pve-node-01:00000001",
        status="stopped",
        exitstatus="OK",
    )

    statuses = [running, running, finished]
    sleep_calls = []

    def get_status(upid):
        return statuses.pop(0)

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    waiter = TaskWaiter(
        get_status=get_status,
        sleep_fn=fake_sleep,
    )

    result = waiter.wait(
        finished.upid,
        interval=0.5,
    )

    assert result == finished
    assert sleep_calls == [0.5, 0.5]

def test_task_waiter_accepts_custom_time_function():
    def get_status(upid):
        return TaskStatus(
            upid=upid,
            status="running",
            exitstatus=None,
        )

    def fake_sleep(seconds):
        pass

    def fake_time():
        return 123.0

    waiter = TaskWaiter(
        get_status=get_status,
        sleep_fn=fake_sleep,
        time_fn=fake_time,
    )

    assert waiter._time is fake_time

def test_task_waiter_raises_timeout_when_task_does_not_finish():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000001",
        status="running",
        exitstatus=None,
    )

    current_time = [0.0]
    sleep_calls = []

    def get_status(upid):
        return task

    def fake_sleep(seconds):
        sleep_calls.append(seconds)
        current_time[0] += seconds

    def fake_time():
        return current_time[0]

    waiter = TaskWaiter(
        get_status=get_status,
        sleep_fn=fake_sleep,
        time_fn=fake_time,
    )

    with pytest.raises(
        TaskTimeoutError,
        match="Task timed out: UPID:pve-node-01:00000001",
    ):
        waiter.wait(
            task.upid,
            interval=1.0,
            timeout=3.0,
        )

    assert sleep_calls == [1.0, 1.0, 1.0]

def test_task_waiter_raises_when_task_finishes_with_error():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000002",
        status="stopped",
        exitstatus="ERROR",
    )

    def get_status(upid):
        return task

    waiter = TaskWaiter(
        get_status=get_status,
    )

    with pytest.raises(
        TaskFailedError,
        match="Task failed: UPID:pve-node-01:00000002",
    ):
        waiter.wait(task.upid)

def test_task_waiter_accepts_task_that_finishes_at_timeout():
    current_time = [0.0]
    sleep_calls = []
    calls = [0]

    def get_status(upid):
        calls[0] += 1

        if current_time[0] >= 3.0:
            return TaskStatus(
                upid=upid,
                status="stopped",
                exitstatus="OK",
            )

        return TaskStatus(
            upid=upid,
            status="running",
            exitstatus=None,
        )

    def fake_sleep(seconds):
        sleep_calls.append(seconds)
        current_time[0] += seconds

    def fake_time():
        return current_time[0]

    waiter = TaskWaiter(
        get_status=get_status,
        sleep_fn=fake_sleep,
        time_fn=fake_time,
    )

    result = waiter.wait(
        "UPID:pve-node-01:00000003",
        interval=1.0,
        timeout=3.0,
    )

    assert result.is_successful
    assert current_time[0] == 3.0
    assert sleep_calls == [1.0, 1.0, 1.0]
    assert calls[0] == 4