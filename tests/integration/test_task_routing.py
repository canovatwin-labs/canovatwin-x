import pytest
from pydantic import ValidationError

from canovatwin.agents import SensorValidator
from canovatwin.policy import Policy
from canovatwin.registry import BY_ID
from canovatwin.runtime import Budget, ExecutionError
from canovatwin.state import AnalysisContext
from canovatwin.supervisor import Supervisor
from canovatwin.task_routing import CapabilityRouter, LocalDispatcher, TaskEnvelope

TASK = {
    "schema_version": "1.0",
    "capability": "quality",
    "incident_id": "INC-test",
    "task_id": "TASK-test-A02",
}


@pytest.mark.parametrize(
    "change",
    [{"schema_version": "2.0"}, {"capability": "unsupported"}, {"task_id": 123}, {"extra": True}],
)
def test_task_envelope_rejects_unsupported_wire_data(change):
    with pytest.raises(ValidationError):
        TaskEnvelope.model_validate(TASK | change)


def test_task_envelope_requires_explicit_schema_version_and_round_trips():
    task = TaskEnvelope.model_validate(TASK)
    assert TaskEnvelope.model_validate_json(task.model_dump_json()) == task
    with pytest.raises(ValidationError):
        TaskEnvelope.model_validate({key: value for key, value in TASK.items() if key != "schema_version"})


def test_router_rejects_ambiguous_claims_and_excludes_planned_agents():
    with pytest.raises(ExecutionError) as error:
        CapabilityRouter((BY_ID["A02"], BY_ID["A03"].model_copy(update={"output_schema": "quality"})))
    assert error.value.code == "AMBIGUOUS_CAPABILITY"

    supervisor = Supervisor()
    planned = BY_ID["A01"].model_copy(update={"output_schema": "quality"})
    with pytest.raises(ExecutionError) as error:
        CapabilityRouter((planned,)).resolve("quality")
    assert error.value.code == "CAPABILITY_UNAVAILABLE"
    assert supervisor._router.resolve("quality") == BY_ID["A02"]


def test_admission_rejects_cross_incident_forged_and_duplicate_tasks(request_factory):
    policy = Policy()
    context = AnalysisContext("INC-test", request_factory(), policy)
    budget = Budget(policy)
    router = CapabilityRouter()
    dispatcher = LocalDispatcher(router, context, budget)
    task = TaskEnvelope.model_validate(TASK)
    for changes in ({"incident_id": "INC-other"}, {"task_id": "TASK-test-F04"}):
        with pytest.raises(ExecutionError) as error:
            dispatcher.admit(task.model_copy(update=changes))
        assert error.value.code == "TASK_SCOPE_MISMATCH"
    with pytest.raises(ValidationError):
        dispatcher.admit(task.model_copy(update={"schema_version": "2.0"}))
    assert budget.agents == 0
    assert dispatcher.admit(task) == BY_ID["A02"]
    with pytest.raises(ExecutionError) as error:
        dispatcher.admit(task)
    assert error.value.code == "DUPLICATE_TASK"
    assert budget.agents == 1
    assert LocalDispatcher(router, context, Budget(policy)).admit(task) == BY_ID["A02"]


def test_runtime_cycle_blocks_before_invoking_the_repeated_specialist(request_factory, monkeypatch):
    monkeypatch.setattr(Supervisor, "_next", staticmethod(lambda *_: "quality"))
    run = Supervisor().run(request_factory())
    assert run.status == "blocked" and run.report is None
    assert run.failure.code == "DUPLICATE_TASK"
    assert [step.tool_calls for step in run.trace] == [1, 0]


def test_unavailable_route_blocks_without_recording_a_phantom_agent(request_factory, monkeypatch):
    supervisor = Supervisor()
    monkeypatch.setattr(supervisor, "_router", CapabilityRouter(()))
    run = supervisor.run(request_factory())
    assert run.status == "blocked" and run.report is None
    assert run.failure.code == "CAPABILITY_UNAVAILABLE"
    assert run.trace == () and run.total_tool_calls == 0


@pytest.mark.parametrize("cancel_in_tool", [False, True])
def test_cooperative_cancellation_blocks_before_publish(request_factory, monkeypatch, cancel_in_tool):
    cancelled = not cancel_in_tool
    original = SensorValidator.execute

    def execute(self, tools):
        nonlocal cancelled
        result = original(self, tools)
        cancelled = True
        return result

    monkeypatch.setattr(SensorValidator, "execute", execute)
    run = Supervisor(cancelled=lambda: cancelled).run(request_factory())
    assert run.status == "blocked" and run.report is None
    assert run.failure.code == "ANALYSIS_CANCELLED"
    assert len(run.trace) == 1
    assert run.total_tool_calls == int(cancel_in_tool)
