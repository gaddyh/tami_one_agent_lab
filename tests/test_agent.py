from src.agent_feature_template.agent import run_agent
from src.agent_feature_template.schemas import AgentInput, Classification, Decision, Priority


def test_agent_classifies_irrelevant_input():
    output = run_agent(AgentInput(input_id="1", text="Promotion newsletter unsubscribe"))

    assert output.classification == Classification.IRRELEVANT
    assert output.should_process is False
    assert output.decision == Decision.IGNORE
    assert output.priority == Priority.NONE


def test_agent_classifies_status_request():
    output = run_agent(AgentInput(input_id="1", text="Can you update me on status?"))

    assert output.classification == Classification.RELEVANT
    assert output.should_process is True
    assert output.decision == Decision.RESPOND
    assert output.priority == Priority.NORMAL
