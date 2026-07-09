from src.agent_feature_template.render import render_outputs
from src.agent_feature_template.schemas import AgentOutput, Classification, Decision, Priority


def test_render_outputs_includes_decision_and_next_step():
    output = AgentOutput(
        input_id="1",
        classification=Classification.RELEVANT,
        should_process=True,
        summary="Input requests a status update.",
        decision=Decision.RESPOND,
        priority=Priority.NORMAL,
        recommended_next_step="Send a short update.",
        confidence=0.8,
        evidence=["Can you update me?"],
    )

    rendered = render_outputs([output])

    assert "status update" in rendered
    assert "decision" in rendered
    assert "Send a short update" in rendered
