from workload_profile_controller.backend import Backend, ResourceStatus


def test_resource_status_contains_expected_states():
    assert ResourceStatus.RUNNING.value == "running"
    assert ResourceStatus.STOPPED.value == "stopped"
    assert ResourceStatus.STARTING.value == "starting"
    assert ResourceStatus.STOPPING.value == "stopping"
    assert ResourceStatus.UNKNOWN.value == "unknown"


def test_backend_defines_get_status():
    assert hasattr(Backend, "get_status")


def test_backend_defines_start():
    assert hasattr(Backend, "start")


def test_backend_defines_stop():
    assert hasattr(Backend, "stop")

class FakeBackend:
    def __init__(self):
        self.resources = {}

    def get_status(self, resource_id: str) -> ResourceStatus:
        return self.resources[resource_id]

    def start(self, resource_id: str) -> None:
        self.resources[resource_id] = ResourceStatus.RUNNING

    def stop(self, resource_id: str) -> None:
        self.resources[resource_id] = ResourceStatus.STOPPED


def test_backend_can_report_resource_status():
    backend = FakeBackend()
    backend.resources["compute"] = ResourceStatus.STOPPED

    assert backend.get_status("compute") == ResourceStatus.STOPPED


def test_backend_can_start_resource():
    backend = FakeBackend()
    backend.resources["compute"] = ResourceStatus.STOPPED

    backend.start("compute")

    assert backend.get_status("compute") == ResourceStatus.RUNNING


def test_backend_can_stop_resource():
    backend = FakeBackend()
    backend.resources["compute"] = ResourceStatus.RUNNING

    backend.stop("compute")

    assert backend.get_status("compute") == ResourceStatus.STOPPED