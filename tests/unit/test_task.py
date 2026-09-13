from workload_profile_controller.backends.proxmox.task import TaskStatus


def test_task_status():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000001:00000001:qmstart:169",
        status="stopped",
        exitstatus="OK",
    )

    assert task.upid == "UPID:pve-node-01:00000001:00000001:qmstart:169"
    assert task.status == "stopped"
    assert task.exitstatus == "OK"


def test_task_status_without_exitstatus():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000001:00000001:qmstart:169",
        status="running",
        exitstatus=None,
    )

    assert task.status == "running"
    assert task.exitstatus is None


def test_task_status_is_not_finished_while_running():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000001:00000001:qmstart:169",
        status="running",
        exitstatus=None,
    )

    assert task.is_finished is False


def test_task_status_is_finished_when_stopped():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000001:00000001:qmstart:169",
        status="stopped",
        exitstatus="OK",
    )

    assert task.is_finished is True


def test_task_status_is_successful_when_stopped_with_ok():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000001:00000001:qmstart:169",
        status="stopped",
        exitstatus="OK",
    )

    assert task.is_successful is True


def test_task_status_is_not_successful_while_running():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000001:00000001:qmstart:169",
        status="running",
        exitstatus=None,
    )

    assert task.is_successful is False


def test_task_status_is_not_successful_when_exitstatus_is_not_ok():
    task = TaskStatus(
        upid="UPID:pve-node-01:00000001:00000001:qmstart:169",
        status="stopped",
        exitstatus="ERROR",
    )

    assert task.is_successful is False